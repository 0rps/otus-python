from qa import models


def trending(request):
    trending = models.Question.objects.all().order_by('-rating', 'date')
    return {'trending_questions': trending}
