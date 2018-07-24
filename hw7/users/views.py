from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_GET, require_http_methods, require_POST


def login(request):
    pass


@require_POST
def logout(request):
    pass


def register(request):
    pass


@require_GET
def account_view(request):
    pass


@require_POST
def change_account_data(request):
    pass


@require_POST
def remove_account_avatar(request):
    pass
