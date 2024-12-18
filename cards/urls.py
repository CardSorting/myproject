from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_card, name='create_card'),
    path('create/<initial_data>', views.create_card, name='create_card_with_data'),
    path('', views.card_list, name='card_list'),
]