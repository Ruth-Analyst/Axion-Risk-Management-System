# gestion/urls.py

from django.urls import path
from gestion import views

urlpatterns = [
    #
    path('', views.index, name='index'),

    #
    path('solicitudes/', views.listado_solicitudes, name='listado_solicitudes'),

    #
    path('solicitudes/valorar/<int:solicitud_id>/', views.valorar_solicitud, name='valorar_solicitud'),

    #
    path('solicitudes/procesar/<int:solicitud_id>/', views.procesar_solicitud, name='procesar_solicitud'),

    #
    path('dashboard/', views.dashboard_factoring, name='dashboard_factoring'),
]