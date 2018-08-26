from django.urls import path, include

from hasker.qa import views as qa_views

urlpatterns = [
    path('', qa_views.index),
    path('qa/', include('hasker.qa.urls')),
    path('users/', include('hasker.users.urls'))
]
