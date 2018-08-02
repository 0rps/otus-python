import datetime

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractBaseUser

from . import models as user_models


class User(AbstractBaseUser):

    USERNAME_FIELD = 'login'

    avatar = models.ImageField(null=True)
    login = models.CharField(max_length=32, null=False)
    email = models.EmailField(null=False)
    password = models.CharField(max_length=256, null=False)
    register_date = models.DateTimeField(null=False)

    @classmethod
    def create_user(cls, cleaned_data):
        user = cls(register_date=datetime.datetime.utcnow(), **cleaned_data)
        user.save()

