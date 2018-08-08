from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.http.response import HttpResponseRedirect, HttpResponseForbidden

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
    count = 5
    query = request.GET.get('q')
    page = request.GET.get('page') or 1

    paginator = Paginator(models.Question.search(query), per_page=count)
    return render(request, 'qa/search.html', {'query': query, 'questions': paginator.get_page(page)})


@require_POST
@login_required(login_url=reverse_lazy('login'))
def star_answer(request, answer_id):
    answer = get_object_or_404(models.Answer, answer_id)
    if answer.author.id == request.user.id:
        return HttpResponseForbidden()


@require_POST
@login_required(login_url=reverse_lazy('login'))
def unstar_answer(request, answer_id):
    answer = get_object_or_404(models.Answer, answer_id)
    if answer.author.id == request.user.id:
        return HttpResponseForbidden()


@login_required(login_url=reverse_lazy('login'))
def vote_answer(request, answer_id):
    is_like = int(request.GET.get('like'))
    is_like = is_like > 0
    answer = get_object_or_404(models.Answer, pk=answer_id)
    # if answer.author.id == request.user.id:
    #     return HttpResponseForbidden()

    answer_likes = models.AnswerLike.objects.filter(answer__id=answer_id).filter(user__id=request.user.id)
    if len(answer_likes) == 0:
        models.AnswerLike.create(answer, request.user, is_like)

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required(login_url=reverse_lazy('login'))
def unvote_answer(request, answer_id):
    answer = get_object_or_404(models.Answer, answer_id)
    if answer.author.id == request.user.id:
        return HttpResponseForbidden()


@require_POST
@login_required(login_url=reverse_lazy('login'))
def vote_question(request, question_id):
    question = get_object_or_404(models.Question, question_id)
    if question.author.id == request.user.id:
        return HttpResponseForbidden()


@require_POST
@login_required(login_url=reverse_lazy('login'))
def unvote_question(request, question_id):
    question = get_object_or_404(models.Question, question_id)
    if question.author.id == request.user.id:
        return HttpResponseForbidden()
