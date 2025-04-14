import requests
import os

class EdificiosModelo:
    def __init__(self):
        self.API_DB = os.environ.get('API_DB')

    def getEdificios(self):
        try:
            respuesta = requests.get(self.API_DB+'/edificios')
            return {"res": 1, "data": respuesta.json()}
        except Exception as e:
            return {"res": 0, "data": str(e)}
    
    def getConsumoEdificios(self, edificio, piso, ambiente, fechaInicio, fechaFin):
        try:
            respuesta = requests.get(self.API_DB + f'/datos?idEdificacion={edificio}&idPiso={piso}&idAmbiente={ambiente}&fechaInicio={fechaInicio}&fechaFin={fechaFin}')
            return {"res": 1, "data": respuesta.json()}
        except Exception as e:
            return {"res": 0, "data": str(e)}
        
    def validarEdificio(self, edificio):
        sql = f"SELECT ID FROM edificio WHERE LOWER(Nombre) = '{edificio}'"
        dato = self.db.consultarDato(sql)

        if dato:
            return dato
        else:
            return None