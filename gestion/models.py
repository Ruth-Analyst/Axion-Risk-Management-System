# gestion/models.py
import cx_Oracle
from datetime import datetime


class FactoringManager:
    """
    """

    def __init__(self):
        #
        self.username = "system"
        self.password = "pythonoracle"
        self.dsn = "localhost/XE"  # Ejemplo: 'localhost:1521/XE'
        self.connection = None
        self._connect()

    def _connect(self):
        try:
            self.connection = cx_Oracle.connect(self.username, self.password, self.dsn)
        except cx_Oracle.Error as error:
            print("Error al conectar a Oracle:", error)
            raise

    def get_all_solicitudes(self):
        """ """
        cursor = self.connection.cursor()
        solicitudes = []
        try:
            cursor.execute("""
                SELECT 
                    sa.id_solicitud, 
                    f.id_factura, 
                    et.razon_social, 
                    f.importe, 
                    sa.fecha_solicitud,
                    es.descripcion AS estado
                FROM Solicitudes_Adelanto sa
                JOIN Facturas f ON sa.id_factura = f.id_factura
                JOIN Empresas_Transporte et ON f.id_empresa = et.id_empresa
                JOIN Estado_Solicitud es ON sa.id_estado = es.id_estado
                WHERE es.descripcion = 'PENDIENTE'
                ORDER BY sa.fecha_solicitud
            """)

            for row in cursor.fetchall():
                solicitudes.append({
                    'id': row[0],
                    'id_factura': row[1],
                    'empresa': row[2],
                    'importe': float(row[3]),
                    'fecha': row[4].strftime("%d/%m/%Y"),
                    'estado': row[5]
                })
        except cx_Oracle.Error as error:
            print("Error al obtener solicitudes:", error)
        finally:
            cursor.close()
            return solicitudes

    # =========================================================================
    #
    # =========================================================================

    def get_datos_valoracion(self, solicitud_id):
        """

        """
        cursor = self.connection.cursor()
        #
        data = {'solicitud': {}, 'empresa': {}, 'deudor': {}}
        try:
            cursor.execute("""
                SELECT 
                    et.id_empresa, 
                    et.razon_social, 
                    et.limite_credito, 
                    et.saldo_actual,
                    et.rating_empresa,          -- Cliente: Solvencia (Rating Propio)
                    et.antiguedad_meses,        -- Cliente: Estabilidad/Fraude
                    et.incidencias_historicas,  -- Cliente: Conformidad
                    f.importe, 
                    f.fecha_vencimiento,
                    f.rating_deudor,            -- Deudor: Solvencia (Rating Crediticio)
                    f.dias_pago_promedio        -- Deudor: Historial de Pago (DPP)
                FROM Solicitudes_Adelanto sa
                JOIN Facturas f ON sa.id_factura = f.id_factura
                JOIN Empresas_Transporte et ON f.id_empresa = et.id_empresa
                WHERE sa.id_solicitud = :id_solicitud
            """, id_solicitud=solicitud_id)

            row = cursor.fetchone()
            if row:
                #
                data['deudor']['rating'] = row[9]
                data['deudor']['dias_pago_promedio'] = int(row[10]) if row[10] else 0

                #
                data['empresa']['id_empresa'] = row[0]
                data['empresa']['razon_social'] = row[1]
                data['empresa']['limite_credito'] = float(row[2])
                data['empresa']['saldo_actual'] = float(row[3])
                data['empresa']['rating_empresa'] = row[4]
                data['empresa']['antiguedad_meses'] = int(row[5]) if row[5] else 0
                data['empresa']['incidencias_historicas'] = int(row[6]) if row[6] else 0

                # Datos de la Solicitud
                data['solicitud']['importe'] = float(row[7])
                data['solicitud']['vencimiento'] = row[8].strftime("%d/%m/%Y")

                # Cálculo de la Exposición (para el dashboard)
                nuevo_saldo = data['empresa']['saldo_actual'] + data['solicitud']['importe']
                data['empresa']['nuevo_saldo_potencial'] = nuevo_saldo

                limite = data['empresa']['limite_credito']
                if limite > 0:
                    data['empresa']['porcentaje_comprometido'] = round((nuevo_saldo / limite) * 100, 2)
                    data['empresa']['excede_limite'] = nuevo_saldo > limite
                else:
                    data['empresa']['porcentaje_comprometido'] = 0.0
                    data['empresa']['excede_limite'] = False

        except cx_Oracle.Error as error:
            print("Error al obtener datos de valoración:", error)
        finally:
            cursor.close()
            return data

    def procesar_solicitud(self, solicitud_id, decision):
        """

        """
        cursor = self.connection.cursor()
        estado = 0  # 1=APROBADA, 2=RECHAZADA

        if decision == 'APROBAR':
            estado = 1
            #
            coste_financiero = (0.05 * 0.95 * self.get_datos_valoracion(solicitud_id)['solicitud']['importe']) + 50
            importe_abonado = self.get_datos_valoracion(solicitud_id)['solicitud']['importe'] - coste_financiero

            try:
                #
                cursor.callproc("PAQUETE_FACT.ACTUALIZAR_SOLICITUD", [solicitud_id, estado])

                #
                #
                cursor.callproc("PAQUETE_FACT.INSERTAR_ANTICIPO", [
                    solicitud_id,
                    datetime.now(),
                    importe_abonado,
                    coste_financiero
                ])

                self.connection.commit()
                return "APROBADA"
            except cx_Oracle.Error as error:
                #
                print("Error al procesar la solicitud (PL/SQL):", error)
                self.connection.rollback()
                return f"ERROR_PLSQL: {str(error)}"

        elif decision == 'RECHAZAR':
            estado = 2
            try:
                #
                cursor.callproc("PAQUETE_FACT.ACTUALIZAR_SOLICITUD", [solicitud_id, estado])
                self.connection.commit()
                return "RECHAZADA"
            except cx_Oracle.Error as error:
                print("Error al rechazar solicitud:", error)
                self.connection.rollback()
                return f"ERROR_PLSQL: {str(error)}"

        return "DECISION_INVALIDA"

    # =========================================================================
    #
    # =========================================================================

    def get_dashboard_data(self):
        """

        """
        cursor = self.connection.cursor()
        chart_data = {'labels': [], 'riesgo': [], 'ganancia_total': 0.0}
        total_ganancia = 0.0
        try:
            #
            cursor.execute("""
                SELECT 
                    et.razon_social,
                    SUM(f.importe) AS riesgo_asumido,
                    SUM(a.coste_financiero) AS ganancia_obtenida
                FROM Anticipos a
                JOIN Facturas f ON a.id_factura = f.id_factura
                JOIN Empresas_Transporte et ON f.id_empresa = et.id_empresa
                GROUP BY et.razon_social
                ORDER BY riesgo_asumido DESC
            """)

            for row in cursor.fetchall():
                chart_data['labels'].append(row[0])
                chart_data['riesgo'].append(float(row[1]))
                total_ganancia += float(row[2])

            chart_data['ganancia_total'] = total_ganancia

        except cx_Oracle.Error as error:
            print("Error al obtener datos del dashboard:", error)
        finally:
            cursor.close()
            return chart_data

    def get_estado_solicitudes_stats(self):
        """

        """
        cursor = self.connection.cursor()
        stats = {'labels': [], 'data': []}
        try:
            cursor.execute("""
                SELECT 
                    es.descripcion,
                    COUNT(sa.id_solicitud)
                FROM Solicitudes_Adelanto sa
                JOIN Estado_Solicitud es ON sa.id_estado = es.id_estado
                GROUP BY es.descripcion
                ORDER BY COUNT(sa.id_solicitud) DESC
            """)

            for row in cursor.fetchall():
                stats['labels'].append(row[0])
                stats['data'].append(int(row[1]))
        except cx_Oracle.Error as error:
            print("Error al obtener estadísticas de estado:", error)
        finally:
            cursor.close()
            return stats

#