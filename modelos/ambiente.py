from db.db import db
import requests

class AmbientesModelo:
    def __init__(self):
        self.db = db()
        self.rutaAPI = "http://192.168.0.114:3000/v1/asistente-virtual"

    def getAmbientes(self, edificio):
        sql = f"SELECT * FROM ambiente WHERE ID_Edificio='{edificio}' ORDER BY Codigo";
        datos = self.db.consultarDatos(sql)

        if datos and len(datos) > 0:
            return datos
        else:
            return None
    
    def validarAmbiente(self, edificio, ambiente):
        sql = f"SELECT Codigo FROM ambiente WHERE ID_Edificio = {edificio} AND Codigo = '{ambiente}'"
        dato = self.db.consultarDato(sql)

        if dato:
            return dato
        else:
            return None
        
    def getAmbientesCompleta(self):
        try:
            response = requests.get(self.rutaAPI+'/edificios')
            data = response.json()  # Si la respuesta es JSON
            return data
        except Exception as e:
            return str(e), 500
        
        sql = f"SELECT Nombre, Codigo FROM ambiente AS a INNER JOIN edificio AS e ON a.ID_Edificio = e.ID;"
        datos = self.db.consultarDatos(sql)

        if datos and len(datos) > 0:
            return datos
        else:
            return None