from modelos.chats import ChatsModelo

class ChatsControlador():
    def __init__(self, app):
        self.modelo = ChatsModelo(app)

    def probarConexion(self):
        return self.modelo.probarConexion()