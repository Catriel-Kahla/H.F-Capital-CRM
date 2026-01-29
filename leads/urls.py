from django.urls import path
from . import views
from .views_recalculate import recalculate_scores

app_name = 'leads'

urlpatterns = [
    path('', views.lead_list, name='lead_list'),
    path('enrich/', views.lead_enrich, name='lead_enrich'),
    path('create/', views.lead_create, name='lead_create'),
    path('clear/', views.clear_leads, name='clear_leads'),
    path('recalculate/', recalculate_scores, name='recalculate_scores'),
    path('<str:pk>/edit/', views.lead_update, name='lead_update'),
    path('<str:pk>/delete/', views.lead_delete, name='lead_delete'),
    path('<str:pk>/view/', views.lead_detail, name='lead_detail'),
]
