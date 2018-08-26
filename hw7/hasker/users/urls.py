from django.urls import path

from . import views


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('<int:user_id>/profile/', views.profile_view, name='profile'),
    path('<int:user_id>/avatar/', views.avatar_view, name='avatar')
]
