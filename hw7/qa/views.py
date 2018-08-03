from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from django.http.response import HttpResponseRedirect

from . import forms
from . import models


@require_GET
def index(request):
    return render(request, 'qa/index.html')


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('login'))
def ask_question(request):
    context = {'hide_ask_button'}

    if request.method == 'GET':
        form = forms.QuestionForm()
    else:
        form = forms.QuestionForm(request.POST)
        if form.is_valid():
            question = models.Question.create(request.user,
                                              )
    context['main_form'] = form
    return render(request, 'qa/ask_question.html', context)


@require_http_methods(['GET', 'POST'])
def question_answers(request, question_id):
    return render(request, 'qa/question_answers.html', {})


@require_GET
def search(request):
    return render(request, 'qa/search.html', {})
