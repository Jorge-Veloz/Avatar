from db.db import db

class EdificiosModelo:
    def __init__(self):
        self.db = db()

    def getEdificios(self):
        sql = f"SELECT * FROM edificio";
        datos = self.db.consultarDatos(sql)

        if datos and len(datos) > 0:
            return datos
        else:
            return None
        
    def validarEdificio(self, edificio):
        sql = f"SELECT ID FROM edificio WHERE LOWER(Nombre) = '{edificio}'"
        dato = self.db.consultarDato(sql)

        if dato:
            return dato
        else:
            return None