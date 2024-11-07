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