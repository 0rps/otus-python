from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods
from django.http.response import HttpResponseRedirect

from . import forms
from . import models


@require_GET
def index(request):
    count = 5
    sort = request.GET.get('sort') or 'date'
    page = request.GET.get('page') or 1

    questions = models.Question.objects.all()

    if sort == 'rating':
        questions = questions.order_by('-rating')
    else:
        questions = questions.order_by('-date')

    paginator = Paginator(questions, per_page=count)
    context = {'questions': paginator.get_page(page), 'sort': sort}

    return render(request, 'qa/index.html', context)


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('login'))
def ask_question(request):
    context = {'hide_ask_button': True}

    if request.method == 'GET':
        form = forms.QuestionForm()
    else:
        form = forms.QuestionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            question = models.Question.create(request.user,
                                              data['title'],
                                              data['body'],
                                              data['tags'])
            return HttpResponseRedirect(reverse('question',
                                                kwargs={'question_id': question.id}))
    context['main_form'] = form
    return render(request, 'qa/ask_question.html', context)


@require_http_methods(['GET', 'POST'])
def question_answers(request, question_id):
    # TODO: make 30
    count = 5

    question = get_object_or_404(models.Question, pk=question_id)
    paginator = Paginator(question.get_answers(), per_page=count)

    if request.method == 'GET':
        page = request.GET.get('page') or 1
        form = forms.AnswerForm()
    else:
        form = forms.AnswerForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            models.Answer.create(request.user,
                                 question,
                                 data['body'])
            form = forms.AnswerForm()
        page = paginator.num_pages

    context = {'question': question,
               'main_form': form,
               'answers': paginator.get_page(page)}

    return render(request, 'qa/question_answers.html', context)


@require_GET
def search(request):

    return render(request, 'qa/search.html', {})
