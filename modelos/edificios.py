import requests
import os
from db.db import PostgresDB

class EdificiosModelo:
    def __init__(self, app):
        self.API_DB = os.environ.get('RUTA_API')
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
    
    def getConsumoEdificiosAsis(self, edificio, piso, ambiente, fechaInicio, fechaFin):
        print("Envio de datos:")
        print(edificio, piso, ambiente, fechaInicio,fechaFin)
        try:
            respuesta = requests.get(self.API_DB + f'/datos?idEdificacion={edificio}&idPiso={piso}&idAmbiente={ambiente}&fechaInicio={fechaInicio}&fechaFin={fechaFin}')
            print("Salida de datos:")
            print(respuesta.json())
            return {"res": 1, "data": respuesta.json()}
        except Exception as e:
            print("Error al consultar:")
            print(e)
            return {"res": 0, "data": str(e)}
        #return {"res": 1, "data": "info obtenida"}

    def getConsumoEdificiosAsisSQL(self, sql):
        print("Impresion de consulta de energia:")
        print(sql)
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
        try:
            respuesta = requests.get(self.API_DB + f'/datos?idEdificacion={edificio}&idPiso={piso}&idAmbiente={ambiente}&fechaInicio={fechaInicio}&fechaFin={fechaFin}')
            print("Salida de datos:")
            print(respuesta.json())
            return {"res": 1, "data": respuesta.json()}
        except Exception as e:
            print("Error al consultar:")
            print(e)
            return {"res": 0, "data": str(e)}
        
    def validarEdificio(self, edificio):
        sql = f"SELECT ID FROM edificio WHERE LOWER(Nombre) = '{edificio}'"
        dato = self.db.consultarDato(sql)

        if dato:
            return dato
        else:
            return None