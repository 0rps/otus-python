from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from django.http.response import HttpResponseRedirect


@require_GET
def index(request):
    return render(request, 'index.html')
