import datetime
from django.db import models
from django.db.models import Q

# Create your models here.


class User(models.Model):

    avatar = models.ImageField(null=True)
    login = models.CharField(max_length=32, null=False)
    email = models.EmailField(null=False)
    password = models.CharField(max_length=256, null=False)
    register_date = models.DateTimeField(null=False)

    @classmethod
    def create_user(cls, cleaned_data):
        user = cls(register_date=datetime.datetime.utcnow(), **cleaned_data)
        user.save()
    #
    # @classmethod
    # def find_user(cls, login_or_email, password):
    #     objs = cls.objects.filter((Q(login__exact=login_or_email)
    #                                | Q(email__exact=login_or_email))
    #                                & Q(password__exact=password))
    #
    #     return objs[0] if len(objs) > 0 else None
