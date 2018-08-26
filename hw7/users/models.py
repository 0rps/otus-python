import datetime

from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.core.mail import send_mail
from django.conf import settings


class User(AbstractBaseUser):

    USERNAME_FIELD = 'login'

    avatar = models.ImageField(null=True)
    login = models.CharField(max_length=32, null=False, unique=True)
    email = models.EmailField(null=False)
    password = models.CharField(max_length=256, null=False)
    register_date = models.DateTimeField(null=False)

    @classmethod
    def create_user(cls, cleaned_data):
        user = cls(register_date=datetime.datetime.utcnow(), **cleaned_data)
        user.save()

        if settings.SEND_EMAIL:
            send_mail("Hasker registration",
                      "Welcome to hasker, mr. {}".format(user.login),
                      settings.EMAIL_HOST_USER, [user.email])

    def update_email_avatar(self, email, avatar):
        if avatar is not None:
            self.avatar = avatar

        if self.email != email:
            self.email = email

        self.save()
