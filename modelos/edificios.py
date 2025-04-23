import requests
import os

class EdificiosModelo:
    def __init__(self):
        self.API_DB = os.environ.get('RUTA_API')

    def getEdificios(self):
        # /!\ Inicia Adaptacion para trabajo remoto sin apis /!\
        return {
            'res': 1,
            'data': {
                'ok': False,
                'observacion': 'Esta es una respuesta falsa generada para hacer pruebas', 
                'datos': None
            }
        }
        # /!\ Acaba Adaptacion para trabajo remoto sin apis /!\
        try:
            respuesta = requests.get(self.API_DB+'/edificios')
            return {"res": 1, "data": respuesta.json()}
        except Exception as e:
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