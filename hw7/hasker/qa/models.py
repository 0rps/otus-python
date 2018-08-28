import datetime

from django.shortcuts import get_object_or_404
from django.db import models, transaction
from django.conf import settings
from django.core.mail import send_mail
from hasker.users import models as user_models


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)


class Question(models.Model):
    title = models.CharField(max_length=128, null=False)
    body = models.TextField()
    date = models.DateTimeField()
    rating = models.IntegerField(default=0)
    answers_count = models.IntegerField(default=0)
    correct_answer_id = models.IntegerField(null=True, default=None)
    author = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)

    @classmethod
    @transaction.atomic
    def create(cls, user, title, body, tags):
        q = cls()
        q.author = user
        q.title = title
        q.body = body
        q.date = datetime.datetime.utcnow()

        q.save()

        for tag_text in tags:
            tag_text = tag_text.lower()
            tag_query_set = Tag.objects.filter(name__exact=tag_text)
            if len(tag_query_set) > 0:
                tag = tag_query_set[0]
            else:
                tag = Tag(name=tag_text)
                tag.save()

            q.tags.add(tag)
        q.save()
        return q

    @classmethod
    def search(cls, query):
        if 'tag:' not in query:
            return cls.objects.filter(models.Q(title__icontains=query) |
                                      models.Q(body__icontains=query)).order_by('-rating', '-date')

        tag_names = [x.strip(',').lower() for x in query.split('tag:') if len(x.strip(',')) > 0]
        if len(tag_names) == 0:
            return []

        tags = []
        for tag_name in tag_names:
            search_results = Tag.objects.filter(name__exact=tag_name)
            if len(search_results) == 0:
                return []
            tags.append(search_results[0])

        return cls.objects.filter(tags__in=[tag.id for tag in tags]).order_by('-rating', '-date')

    def get_answers(self):
        return Answer.objects.filter(question__id=self.id).order_by('-rating', 'date')

    @transaction.atomic
    def set_correct_answer(self, answer):
        self.correct_answer_id = answer.id
        self.save()

    @transaction.atomic
    def cancel_correct_answer(self):
        self.correct_answer_id = None
        self.save()

    def time_ago_str(self):
        delta = datetime.datetime.now(datetime.timezone.utc) - self.date
        delta = delta.seconds

        if delta // (24 * 3600) > 0:
            delta = delta // (24 * 3600)
            unit, units = 'day', 'days'
        elif delta // 3600 > 0:
            delta = delta // 3600
            unit, units = 'hour', 'hours'
        elif delta // 60 > 0:
            delta = delta // 60
            unit, units = 'minute', 'minutes'
        else:
            unit, units = 'second', 'seconds'

        if delta > 1:
            msg = "{} {}".format(delta, units)
        else:
            msg = "{} {}".format(delta, unit)

        return msg


class Answer(models.Model):
    body = models.TextField()
    date = models.DateTimeField(default=datetime.datetime.utcnow)
    rating = models.IntegerField(default=0)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    author = models.ForeignKey(user_models.User, on_delete=models.CASCADE)

    @classmethod
    def create(cls, user, question, body):
        answer = cls()
        answer.author = user
        answer.question = question
        answer.body = body
        answer.save()

        question.answers_count += 1
        question.save()

        if settings.SEND_EMAIL:
            send_mail("You have one answer on Hasker",
                      "User '{}' answered your question '{}'"
                      .format(user.login, question.title),
                      settings.EMAIL_HOST_USER, [question.author.email])

        return answer


class Like(models.Model):
    TYPE_ANSWER = 'answer'
    TYPE_QUESTION = 'question'

    user = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    object_id = models.IntegerField()
    object_type = models.CharField(max_length=max(len(TYPE_ANSWER), len(TYPE_QUESTION)))
    is_like = models.BooleanField()

    @classmethod
    @transaction.atomic
    def create(cls, _object, object_type, user, is_like):
        if object_type != cls.TYPE_ANSWER and object_type != cls.TYPE_QUESTION:
            raise ValueError('Unknown object type for like')

        if is_like:
            _object.rating += 1
        else:
            _object.rating -= 1

        like = cls()
        like.object_type = object_type
        like.object_id = _object.id
        like.user = user
        like.is_like = is_like

        like.save()
        _object.save()

    @transaction.atomic
    def cancel_like(self):
        if self.object_type == self.TYPE_QUESTION:
            _object = get_object_or_404(Question, pk=self.object_id)
        else:
            _object = get_object_or_404(Answer, pk=self.object_id)

        if self.is_like:
            _object.rating -= 1
        else:
            _object.rating += 1
        self.delete()
        _object.save()

    @classmethod
    def find_answer_likes(cls, answer_id, user_id=None):
        return cls._find_likes(answer_id, cls.TYPE_ANSWER, user_id)

    @classmethod
    def find_question_likes(cls, question_id, user_id=None):
        return cls._find_likes(question_id, cls.TYPE_QUESTION, user_id)

    @classmethod
    def question_answer_likes(cls, user, answer_ids):
        result = cls.objects.filter(user__id=user.id)\
            .filter(object_type__exact=cls.TYPE_ANSWER)\
            .filter(object_id__in=answer_ids)

        return {r.object_id: r for r in result}

    @classmethod
    def _find_likes(cls, object_id, object_type, user_id):
        qs = cls.objects.filter(object_id=object_id) \
            .filter(object_type__exact=object_type)

        if user_id:
            qs = qs.filter(user__id=user_id)

        return qs
