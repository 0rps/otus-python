from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from . import forms as user_forms
from . import models as user_models


@require_http_methods(['GET', 'POST'])
def signup_view(request):
    if request.method == 'GET':
        form = user_forms.SignupForm()
    else:
        form = user_forms.SignupForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user_models.User.create_user(data)
            return HttpResponseRedirect('/')

    return render(request, 'signup.html', {'main_form': form})


@require_http_methods(['GET', 'POST'])
def login_view(request):
    login_failed = False
    if request.method == 'GET':
        form = user_forms.LoginForm()
    else:
        form = user_forms.LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = user_models.User.authenticate_user(**data)
            if user is not None:
                if hasattr(request, 'user'):
                    request.user = user
                return HttpResponseRedirect('/')
            else:
                login_failed = True

    return render(request, 'login.html', {'main_form': form,
                                          'login_failed': login_failed})


@require_POST
def logout_view(request):
    pass


@require_GET
def profile_view(request):
    pass


@require_POST
def change_account_data(request):
    pass


@require_POST
def remove_account_avatar(request):
    pass
