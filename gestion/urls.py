# gestion/urls.py

from django.urls import path
from gestion import views

urlpatterns = [
    # Ruta principal (opcional)
    path('', views.index, name='index'),

    # Listado de Solicitudes
    path('solicitudes/', views.listado_solicitudes, name='listado_solicitudes'),

    # DASHBOARD DE VALORACIÓN
    path('solicitudes/valorar/<int:solicitud_id>/', views.valorar_solicitud, name='valorar_solicitud'),

    # PROCESAMIENTO DE LA DECISIÓN FINAL
    path('solicitudes/procesar/<int:solicitud_id>/', views.procesar_solicitud, name='procesar_solicitud'),

    # Dashboard principal (Estadísticas)
    path('dashboard/', views.dashboard_factoring, name='dashboard_factoring'),
]