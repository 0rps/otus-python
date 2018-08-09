from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.http.response import HttpResponseRedirect, HttpResponseForbidden, HttpResponseBadRequest

from . import forms
from . import models
from . import constants


@require_GET
def index(request):
    sort = request.GET.get('sort') or 'date'
    page = request.GET.get('page') or 1

    questions = models.Question.objects.all()

    if sort == 'rating':
        questions = questions.order_by('-rating')
    else:
        questions = questions.order_by('-date')

    paginator = Paginator(questions,
                          per_page=constants.index_questions_per_page)
    context = {'questions': paginator.get_page(page), 'sort': sort}
    return render(request, 'qa/index.html', context)


@require_http_methods(['GET', 'POST'])
@login_required(login_url=reverse_lazy('login'))
def ask_question(request):
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
    return render(request, 'qa/ask_question.html', {
        'hide_ask_button': True,
        'main_form': form
    })


@require_http_methods(['GET', 'POST'])
def question_answers(request, question_id):
    question = get_object_or_404(models.Question, pk=question_id)
    paginator = Paginator(question.get_answers(),
                          per_page=constants.answers_per_page)

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

    q_like = models.QuestionLike.objects\
        .filter(question__id=question_id)\
        .filter(user__id=request.user.id)
    q_like = q_like[0] if len(q_like) > 0 else None
    a_like = models.AnswerLike.question_answer_like(request.user, question)

    context = {'question': question,
               'main_form': form,
               'answers': paginator.get_page(page),
               'question_rated': q_like,
               'question_rated_up': q_like and q_like.is_like,
               'question_rated_down': q_like and not q_like.is_like,
               'answer_rated': a_like and a_like.answer.id,
               'answer_rated_up': a_like and a_like.is_like,
               'answer_rated_down': a_like and not a_like.is_like
               }

    return render(request, 'qa/question_answers.html', context)


@require_GET
def search(request):
    query = request.GET.get('q')
    page = request.GET.get('page') or 1

    paginator = Paginator(models.Question.search(query),
                          per_page=constants.search_results_per_page)
    return render(request, 'qa/search.html', {
        'query': query,
        'questions': paginator.get_page(page)
    })


@login_required(login_url=reverse_lazy('login'))
def star_answer(request, answer_id):
    answer = get_object_or_404(models.Answer, pk=answer_id)
    if answer.question.author.id != request.user.id:
        return HttpResponseForbidden()

    answer.question.set_correct_answer(answer)
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required(login_url=reverse_lazy('login'))
def unstar_answer(request, answer_id):
    answer = get_object_or_404(models.Answer, pk=answer_id)
    if answer.question.author.id != request.user.id:
        return HttpResponseForbidden()

    answer.question.cancel_correct_answer()
    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required(login_url=reverse_lazy('login'))
def vote_answer(request, answer_id):
    try:
        is_like = int(request.GET.get('like'))
    except ValueError:
        return HttpResponseBadRequest()
    is_like = is_like > 0
    answer = get_object_or_404(models.Answer, pk=answer_id)

    # if answer.author.id == request.user.id:
    #     return HttpResponseForbidden()

    answer_likes = models.AnswerLike.objects.filter(answer__id=answer_id).filter(user__id=request.user.id)
    if len(answer_likes) == 0:
        models.AnswerLike.create(answer, request.user, is_like)
    else:
        return HttpResponseForbidden()

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required(login_url=reverse_lazy('login'))
def unvote_answer(request, answer_id):
    result = models.AnswerLike.objects.filter(answer__id=answer_id)
    if len(result) > 0:
        like = result[0]
        like.cancel_like()

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required(login_url=reverse_lazy('login'))
def vote_question(request, question_id):
    try:
        is_like = int(request.GET.get('like'))
    except ValueError:
        return HttpResponseBadRequest()

    is_like = is_like > 0
    question = get_object_or_404(models.Question, pk=question_id)
    # if answer.author.id == request.user.id:
    #     return HttpResponseForbidden()

    question_likes = models.QuestionLike.objects\
        .filter(question__id=question_id)\
        .filter(user__id=request.user.id)
    if len(question_likes) == 0:
        models.QuestionLike.create(question, request.user, is_like)
    else:
        return HttpResponseForbidden()

    return HttpResponseRedirect(request.META['HTTP_REFERER'])


@login_required(login_url=reverse_lazy('login'))
def unvote_question(request, question_id):
    result = models.QuestionLike.objects.filter(question__id=question_id)
    if len(result) > 0:
        result[0].cancel_like()

    return HttpResponseRedirect(request.META['HTTP_REFERER'])
