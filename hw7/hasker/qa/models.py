import datetime

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
    has_correct_answer = models.BooleanField(default=False)
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
        answer.is_correct = True
        self.has_correct_answer = True

        answer.save()
        self.save()

    @transaction.atomic
    def cancel_correct_answer(self):
        answer_set = Answer.objects.filter(question__id=self.id).filter(is_correct=True)
        if len(answer_set) == 0:
            return

        answer = answer_set[0]
        answer.is_correct = False
        answer.save()

        self.has_correct_answer = False
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
    is_correct = models.BooleanField(default=False)
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


class QuestionLike(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    is_like = models.BooleanField()

    @classmethod
    @transaction.atomic
    def create(cls, question, user, is_like):
        if is_like:
            question.rating += 1
        else:
            question.rating -= 1

        like = cls()
        like.question = question
        like.user = user
        like.is_like = is_like

        like.save()
        question.save()

    @transaction.atomic
    def cancel_like(self):
        if self.is_like:
            self.question.rating -= 1
        else:
            self.question.rating += 1
        self.delete()
        self.question.save()


class AnswerLike(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    is_like = models.BooleanField()

    @classmethod
    @transaction.atomic
    def create(cls, answer, user, is_like):
        if is_like:
            answer.rating += 1
        else:
            answer.rating -= 1

        like = cls()
        like.answer = answer
        like.user = user
        like.is_like = is_like

        like.save()
        answer.save()

    @classmethod
    def question_answer_like(cls, user, question):
        result = cls.objects.filter(answer__question__id=question.id).filter(user__id=user.id)
        return None if len(result) == 0 else result[0]

    @transaction.atomic
    def cancel_like(self):
        if self.is_like:
            self.answer.rating -= 1
        else:
            self.answer.rating += 1
        self.delete()
        self.answer.save()
