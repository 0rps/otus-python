from django.shortcuts import render
from django.views.decorators.http import require_GET

from users import forms as user_forms
# Create your views here.


def index(request):
    form = user_forms.SignupForm()
    return render(request, 'signup.html', {'signup_form': form})
