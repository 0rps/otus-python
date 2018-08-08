"""hw7 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from . import views


urlpatterns = [
    path('', views.index),
    path('admin/', admin.site.urls),
    path('qa/ask/', views.ask_question, name='ask'),
    path('qa/question/<int:question_id>/', views.question_answers, name='question'),
    path('qa/search/', views.search, name='search'),
    path('users/', include('users.urls')),
    path('qa/question/<int:question_id>/vote', views.vote_question, name='question_vote'),
    path('qa/question/<int:question_id>/unvote', views.unvote_question, name='question_unvote'),
    path('qa/answer/<int:answer_id>/vote', views.vote_answer, name='answer_vote'),
    path('qa/answer/<int:answer_id>/unvote', views.unstar_answer, name='answer_unvote'),
    path('qa/answer/<int:answer_id>/star', views.star_answer, name='answer_star'),
    path('qa/answer/<int:answer_id>/unstar', views.unstar_answer, name='answer_unstar')

]
