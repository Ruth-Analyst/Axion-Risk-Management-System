# gestion/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from gestion.models import FactoringManager
import json


# =========================================================================
# VISTA PRINCIPAL
# =========================================================================

def index(request):
    return render(request, 'gestion/index.html')


# =========================================================================
# VISTA DE LISTADO
# =========================================================================

def listado_solicitudes(request):
    manager = FactoringManager()
    solicitudes = manager.get_all_solicitudes()
    return render(request, 'gestion/listado_solicitudes.html', {'solicitudes': solicitudes})


# =========================================================================
# DASHBOARD DE VALORACIÓN
# =========================================================================

def valorar_solicitud(request, solicitud_id):
    manager = FactoringManager()

    #  5 métricas de riesgo desde el Manager
    datos_valoracion = manager.get_datos_valoracion(solicitud_id)

    # Pasar los datos al template
    return render(request, 'gestion/dashboard_factoring.html', {
        'datos': datos_valoracion,
        'solicitud_id': solicitud_id,
        #
    })


# =========================================================================
# PROCESAMIENTO DE LA DECISIÓN
# =========================================================================

def procesar_solicitud(request, solicitud_id):
    if request.method == 'POST':
        manager = FactoringManager()
        # La decisión viene del formulario POST
        decision = request.POST.get('decision')

        resultado = manager.procesar_solicitud(solicitud_id, decision)

        # Redirigir al listado con un mensaje de estado
        return redirect(reverse('listado_solicitudes'))  # O puedes redirigir a una página de confirmación

    # Si alguien intenta acceder sin POST, redirigir al listado
    return redirect(reverse('listado_solicitudes'))


# =========================================================================
# DASHBOARD DE ESTADÍSTICAS
# =========================================================================

def dashboard_factoring(request):
    manager = FactoringManager()
    chart_data = manager.get_dashboard_data()
    estado_stats = manager.get_estado_solicitudes_stats()

    return render(request, 'gestion/dashboard_factoring.html', {
        'chart_data': json.dumps(chart_data),
        'estado_stats': json.dumps(estado_stats)
    })