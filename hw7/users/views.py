from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

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

    return render(request, 'users/signup.html', {'main_form': form})


@require_http_methods(['GET', 'POST'])
def login_view(request):
    auth_failed = False
    if request.method == 'GET':
        form = user_forms.LoginForm()
    else:
        form = user_forms.LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(request, **data)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/')

            auth_failed = True

    return render(request, 'users/login.html', {'main_form': form,
                                                'auth_failed': auth_failed})


# TODO: login required
@require_POST
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)

    return HttpResponseRedirect('/')


# TODO: login required
def profile_view(request, user_id):
    if user_id == request.user.id:
        if request.method == 'GET':
            form = user_forms.ProfileForm()
        else:
            form = user_forms.ProfileForm(request.POST)
            if form.is_valid():
                    return HttpResponseRedirect('/')

        return render(request, 'users/change_profile.html', {'main_form': form})

    elif request.method == 'GET':
        another_user = get_object_or_404(user_models.User, pk=user_id)
        return render(request, 'users/profile.html', {'profile_user': another_user})

    return HttpResponseForbidden()


@require_GET
def avatar_view(request, user_id):
    pass