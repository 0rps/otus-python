from django.db import models
from users import models as user_models


class Tag(models.Model):
    name = models.CharField(max_length=64)


class Question(models.Model):
    title = models.CharField(max_length=128)
    body = models.TextField()
    date = models.DateTimeField()
    rating = models.IntegerField(default=0)
    answers_count = models.IntegerField(default=0)
    author = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag)


class Answer(models.Model):
    body = models.TextField()
    date = models.DateTimeField()
    rating = models.IntegerField(default=0)
    is_correct = models.BooleanField(default=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    author = models.ForeignKey(user_models.User, on_delete=models.CASCADE)


class QuestionLike(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    is_like = models.BooleanField()


class AnswerLike(models.Model):
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.CASCADE)
    is_like = models.BooleanField()

