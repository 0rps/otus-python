from django.urls import path, include

from qa import views as qa_views

urlpatterns = [
    path('', qa_views.index),
    path('qa/', include('qa.urls')),
    path('users/', include('users.urls'))
]
