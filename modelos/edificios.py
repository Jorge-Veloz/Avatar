import requests
import os
from db.db import PostgresDB
from functools import reduce

class EdificiosModelo:
    def __init__(self, app):
        self.db = PostgresDB(app, os.getenv("PG_DBSB"))

    def getEdificios(self):
        resultado = {
            'ok': True,
            'datos': None,
            'observacion': None
        }
        sql = """
            SELECT id, idempresa, empresa, edificacion, (
                SELECT json_agg(json_build_object(
                    'id', X.id,
                    'nombre',X.piso,
                    'ambientes', (SELECT json_agg(json_build_object(
                        'id', Y.id,
                        'nombre',Y.ambiente,
                        'tipoAmbiente',Y.tipo_ambiente
                    ) ORDER BY id ASC) FROM administracion.vmostrarambientes Y WHERE Y.idpiso = X.id AND Y.estado)
                ) ORDER BY id ASC) FROM administracion.vmostrarpisos X WHERE X.idedificacion = A.id AND X.estado
            ) AS pisos FROM administracion.vmostraredificaciones AS A WHERE idempresa = 2 AND estado ORDER BY id DESC
        """
        try:
            #respuesta = requests.get(self.API_DB+'/edificios')
            resultado['datos'] = self.db.consultarDatos(sql)
            return {"res": 1, "data": resultado}
        except Exception as e:
            return {"res": 0, "data": str(e)}
    
    
    def getConsumoEdificiosAsisSQL(self, sql):
        print("Impresion de consulta de energia:")
        print(sql)
        try:
            datos = self.db.consultarDatos(sql)
            return {"res": 1, "data": {'ok':True, 'datos':self.construirObjetoConsumo(datos)}}
        except Exception as e:
            print("Error al consultar:")
            print(e)
            return {"res": 0, "data": str(e)}

    def construirObjetoConsumo(self, datos):
        consumoAmbiente = {
            'amperio': sum(d['total_amperio'] for d in datos if d['total_amperio']),
            'kilovatio': sum(d['total_kilovatio'] for d in datos if d['total_kilovatio'])
        }

        consumoEdificio = sum(d['total_kilovatio_edificio'] for d in datos if d['total_kilovatio_edificio'])

        datosConsumo = [
            {
                'amperio': d['total_amperio'] or 0.00,
                'kilovatio': d['total_kilovatio'] or 0.00,
                'fecha': d['fecha'],
                'totalKilovatioEdificio': d['total_kilovatio_edificio'] or 0.00,
            } for d in datos
        ]

        objetoConsumo = {
            'consumoAmbiente': consumoAmbiente,
            'consumoEdificio': consumoEdificio,
            'datos': datosConsumo
        }

        return objetoConsumo
    
    def consumoSemana(self, edificio, piso, ambiente, fechaInicio, fechaFin):
        print("Envio de datos:")
        print(edificio, piso, ambiente, fechaInicio,fechaFin)
        sql = f""
        try:
            datos = self.db.consultarDatos(sql)
            return {"res": 1, "data": {'ok':True, 'datos':datos}}
        except Exception as e:
            print("Error al consultar:")
            print(e)
            return {"res": 0, "data": str(e)}

    def getConsumoEdificios(self, edificio, piso, ambiente, fechaInicio, fechaFin):
        print("Envio de datos:")
        print(edificio, piso, ambiente, fechaInicio,fechaFin)
        sql = f"WITH agrupados AS (SELECT DATE(fecha_creacion) AS fecha, SUM(amperio) AS total_amperio, SUM(kilovatio) AS total_kilovatio FROM monitoreo.vmostrardatoselectricidad WHERE idempresa = 2 AND idedificacion = {edificio} AND idpiso = {piso} AND idambiente = {ambiente} AND DATE(fecha_creacion) >= '{fechaInicio}' AND DATE(fecha_creacion) <= '{fechaFin}' GROUP BY DATE(fecha_creacion)) SELECT g.fecha::TEXT, g.total_amperio, g.total_kilovatio, (SELECT SUM(B.kilovatio) FROM monitoreo.vmostrardatoselectricidad AS B WHERE B.idedificacion = {edificio} AND DATE(B.fecha_creacion) = g.fecha) AS total_kilovatio_edificio FROM agrupados g ORDER BY g.fecha ASC;"
        try:
            datos = self.db.consultarDatos(sql)
            return {"res": 1, "data": {'ok':True, 'datos':self.construirObjetoConsumo(datos)}}
        except Exception as e:
            print("Error al consultar:")
            print(e)
            return {"res": 0, "data": str(e)}
        
     