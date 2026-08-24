from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('sale/add/', views.add_sale, name='add_sale'),
    path('sale/edit/<int:pk>/', views.edit_sale, name='edit_sale'),
    path('sale/delete/<int:pk>/', views.delete_sale, name='delete_sale'),
    path('sale/<int:pk>/', views.sale_detail, name='sale_detail'),
    path('participant/add/', views.add_participant, name='add_participant'),
    path('participant/edit/<int:pk>/', views.edit_participant, name='edit_participant'),
    path('participant/delete/<int:pk>/', views.delete_participant, name='delete_participant'),
    path('participant/<int:pk>/', views.participant_detail, name='participant_detail'),
    path('trees/', views.tree_list, name='tree_list'),
    path('tree/add/', views.add_tree, name='add_tree'),
    path('tree/edit/<int:pk>/', views.edit_tree, name='edit_tree'),
    path('tree/delete/<int:pk>/', views.delete_tree, name='delete_tree'),
    path('request/add/', views.add_tree_request, name='add_tree_request'),
    path('requests/', views.tree_requests_list, name='tree_requests_list'),
    path('request/confirm/<int:pk>/', views.confirm_request, name='confirm_request'),
    path('request/cancel/<int:pk>/', views.cancel_request, name='cancel_request'),
    path('statistics/', views.statistics, name='statistics'),
]