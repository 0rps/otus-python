from django.db import models

# Create your models here.


class User(models.Model):

    avatar = models.ImageField(null=True)
    login = models.CharField(max_length=32, null=False)
    email = models.EmailField(null=False)
    password = models.CharField(max_length=256, null=False)
    register_date = models.DateTimeField(null=False)

    def register(self):
        pass

    def login(self):
        pass
