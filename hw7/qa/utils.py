from qa import models


def trending_context_processor(_):
    trending = models.Question.objects.all().order_by('-rating', '-date')
    return {'trending_questions': trending}
