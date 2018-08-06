import mimetypes

from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404
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
            if 'avatar' in request.FILES:
                data['avatar'] = request.FILES['avatar']
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
            user = authenticate(request,
                                username=data['login'],
                                password=data['password'])
            if user is not None:
                login(request, user)
                return HttpResponseRedirect('/')

            auth_failed = True

    return render(request, 'users/login.html', {'main_form': form,
                                                'auth_failed': auth_failed})


@require_POST
@login_required(login_url=reverse_lazy('login'))
def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/')


@require_http_methods(['POST', 'GET'])
@login_required(login_url=reverse_lazy('login'))
def profile_view(request, user_id):
    if user_id != request.user.id:
        return HttpResponseForbidden()

    if request.method == 'GET':
        form = user_forms.ProfileForm()
    else:
        form = user_forms.ProfileForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if 'avatar' in request.FILES:
                data['avatar'] = request.FILES['avatar']
            else:
                data['avatar'] = None
            request.user.update_email_avatar(**data)
            form = user_forms.ProfileForm(request.POST)

    return render(request, 'users/profile.html', {'main_form': form})


@require_GET
@login_required(login_url=reverse_lazy('login'))
def avatar_view(request, user_id):
    user = get_object_or_404(user_models.User, pk=user_id)
    if user and user.avatar:
        image = user.avatar
        mimetype = mimetypes.guess_type(image.url)[0]
        response = HttpResponse(image, content_type=mimetype)
        return response

    raise Http404

