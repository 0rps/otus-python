from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from django.http.response import HttpResponseRedirect
from django.contrib.auth import authenticate, login as django_login, user_logged_in

from users import forms as user_forms
from users import models as user_models
# Create your views here.


@require_http_methods(['GET', 'POST'])
def signup(request):
    if request.method == 'GET':
        form = user_forms.SignupForm()
    else:
        form = user_forms.SignupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user_models.User.create_user(data)
            return HttpResponseRedirect('/')

    return render(request, 'signup.html', {'signup_form': form})


@require_http_methods(['GET', 'POST'])
def login(request):
    login_failed = False
    if request.method == 'GET':
        form = user_forms.LoginForm()
    else:
        form = user_forms.LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(request, **data)
            if user is not None:
                if hasattr(request, 'user'):
                    request.user = user
                return HttpResponseRedirect('/')
            else:
                login_failed = True

    return render(request, 'login.html', {'login_form': form,
                                          'login_failed': login_failed})


@require_GET
def index(request):
    return render(request, 'index.html')
