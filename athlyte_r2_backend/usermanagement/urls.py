from django.urls import path
from .views import *

urlpatterns = [
    path('login/', authenticate_user, name='authenticate-user'),
    path('create/', create_user, name='create-user')
]