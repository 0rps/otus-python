from django.urls import path, re_path

from . import views


urlpatterns = [
    path('login/', views.login_view),
    path('signup/', views.signup_view),
    re_path(r'^profile/(?P<id>\d+)/$', views.profile_view)
]
