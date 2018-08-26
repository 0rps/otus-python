from django.db.models import Q, ObjectDoesNotExist
from . import models


class SimpleAuthBackend:
    def authenticate(self, request, username=None, password=None):
        users = models.User.objects.filter(Q(login__exact=username)
                                           & Q(password__exact=password))
        return users[0] if len(users) > 0 else None

    def get_user(self, user_id):
        try:
            return models.User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None
