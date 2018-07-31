from django.db.models import Q, ObjectDoesNotExist
from . import models as user_models


class SimpleAuthBackend:

    def authenticate(self, request, username=None, password=None):
        users = user_models.User.objects.filter((Q(login__exact=username)
                                                | Q(email__exact=username))
                                                & Q(password__exact=password))
        return users[0] if len(users) > 0 else None

    def get_user(self, user_id):
        try:
            return user_models.User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None
