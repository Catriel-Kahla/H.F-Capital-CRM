from django.urls import path
from . import views
from .views_changelog import changelog

app_name = 'crm'

urlpatterns = [
    path('', views.home, name='home'),
    path('import/', views.import_csv, name='import_csv'),
    path('ai-enrichment/', views.ai_enrichment, name='ai_enrichment'),
    path('ai-enrichment/stream/', views.ai_enrichment_stream, name='ai_enrichment_stream'),
    path('enrichment-progress/', views.enrichment_progress, name='enrichment_progress'),
    path('changelog/', changelog, name='changelog'),
]
