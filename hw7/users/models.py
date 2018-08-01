import datetime
from django.db import models
from django.db.models import Q

from . import models as user_models
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

    @classmethod
    def authenticate_user(cls, username, password):
        users = user_models.User.objects.filter((Q(login__exact=username)
                                                 | Q(email__exact=username))
                                                & Q(password__exact=password))
        return users[0] if len(users) > 0 else None

