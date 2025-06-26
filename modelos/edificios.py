import requests
import os
from db.db import PostgresDB

class EdificiosModelo:
    def __init__(self, app):
        self.API_DB = os.environ.get('RUTA_API')
        self.db = PostgresDB(app, os.getenv("PG_DBSB"))

    def getEdificios(self):
        try:
            respuesta = requests.get(self.API_DB+'/edificios')
            return {"res": 1, "data": respuesta.json()}
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
            return {"res": 1, "data": datos}
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