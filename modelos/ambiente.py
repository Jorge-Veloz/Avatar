from db.db import db

class AmbientesModelo:
    def __init__(self):
        self.db = db()

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
        sql = f"SELECT Nombre, Codigo FROM ambiente AS a INNER JOIN edificio AS e ON a.ID_Edificio = e.ID;"
        datos = self.db.consultarDatos(sql)

        if datos and len(datos) > 0:
            return datos
        else:
            return None