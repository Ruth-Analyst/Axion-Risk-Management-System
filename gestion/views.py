# gestion/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from gestion.models import FactoringManager
import json




def index(request):
    return render(request, 'gestion/index.html')




def listado_solicitudes(request):
    manager = FactoringManager()
    solicitudes = manager.get_all_solicitudes()
    return render(request, 'gestion/listado_solicitudes.html', {'solicitudes': solicitudes})




def valorar_solicitud(request, solicitud_id):
    manager = FactoringManager()


    datos_valoracion = manager.get_datos_valoracion(solicitud_id)


    return render(request, 'gestion/dashboard_factoring.html', {
        'datos': datos_valoracion,
        'solicitud_id': solicitud_id,

    })




def procesar_solicitud(request, solicitud_id):
    if request.method == 'POST':
        manager = FactoringManager()
        #
        decision = request.POST.get('decision')

        resultado = manager.procesar_solicitud(solicitud_id, decision)

        #
        return redirect(reverse('listado_solicitudes'))  #

    #
    return redirect(reverse('listado_solicitudes'))


# =========================================================================
#
# =========================================================================

def dashboard_factoring(request):
    manager = FactoringManager()
    chart_data = manager.get_dashboard_data()
    estado_stats = manager.get_estado_solicitudes_stats()

    return render(request, 'gestion/dashboard_factoring.html', {
        'chart_data': json.dumps(chart_data),
        'estado_stats': json.dumps(estado_stats)
    })