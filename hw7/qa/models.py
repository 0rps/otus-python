import datetime

from django.db import models
from users import models as user_models


class Tag(models.Model):
    name = models.CharField(max_length=64, unique=True)


class Question(models.Model):
    title = models.CharField(max_length=128, null=False)
    body = models.TextField()
    date = models.DateTimeField(default=datetime.datetime.utcnow)
    rating = models.IntegerField(default=0)
    answers_count = models.IntegerField(default=0)
    author = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)

    @classmethod
    def create(cls, user, title, body, tags):
        q = cls()
        q.author = user
        q.title = title
        q.body = body

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

    def get_answers(self):
        return Answer.objects.filter(question__id=self.id)


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

        return answer


class QuestionLike(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    is_like = models.BooleanField()


class AnswerLike(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    is_like = models.BooleanField()

