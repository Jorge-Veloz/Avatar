from db.db import PostgresDB

class ChatsModelo:
    def __init__(self, app):
        self.db = PostgresDB(app)
        #self.db.app = None  # Asignar la aplicación a la instancia de PostgresDB
    
    def probarConexion(self):
        return self.db.probarConexion()