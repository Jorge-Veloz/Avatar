from modelos.chats import ChatsModelo
import json

class ChatsControlador():
    def __init__(self, app):
        self.modelo = ChatsModelo(app)

    def enviarMensaje(self, idHilo, mensaje):
        # if mensaje['role'] == 'tool' and 'content' in mensaje and mensaje['content']:
        #     mensaje['content'] = json.load(mensaje['content'])
        mensajeJson = json.dumps(mensaje)
        resultado = self.modelo.enviarMensaje(idHilo, mensajeJson)
        return resultado[0][0]
    
    def getHistorialMensajes(self, idHilo):
        mensajes = self.modelo.getHistorialMensajes(idHilo)
        #return json.load(mensajes)
        hmensajes = [m['datos'] for m in mensajes]
        return hmensajes

    def crearHilo(self):
        idHilo = self.modelo.getIdHilo()
        return idHilo

    def probarConexion(self):
        return self.modelo.probarConexion()