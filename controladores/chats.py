from modelos.chats import ChatsModelo
import json

class ChatsControlador():
    def __init__(self, app):
        self.modelo = ChatsModelo(app)

    def enviarMensaje(self, idHilo, mensajes, categoria='general'):
        # if mensaje['role'] == 'tool' and 'content' in mensaje and mensaje['content']:
        #     mensaje['content'] = json.load(mensaje['content'])
        respuesta = {"ok": False}
        for msg in mensajes:
            mensajeJson = json.dumps(msg)
            resultado = self.modelo.enviarMensaje(idHilo, mensajeJson, categoria)
            print(resultado)
            respuesta = resultado[0][0]
        return respuesta
    
    def reaccionarMensaje(self, idHilo, idMensaje, reaccion):
        # if mensaje['role'] == 'tool' and 'content' in mensaje and mensaje['content']:
        #     mensaje['content'] = json.load(mensaje['content'])
        resultado = self.modelo.reaccionarMensaje(idHilo, idMensaje, reaccion)
        return resultado[0][0]
    
    def getListaMensajes(self, idHilo):
        return self.modelo.getListaMensajes(idHilo)
        #return json.load(mensajes)
        #hmensajes = [m['datos'] for m in mensajes]
        #return hmensajes
    
    def getHistorialMensajes(self, idHilo):
        mensajes = self.modelo.getHistorialMensajes(idHilo)
        #return json.load(mensajes)
        hmensajes = [m['datos'] for m in mensajes]
        return hmensajes
    
    def getHistorialMensajesConsumo(self, idHilo):
        mensajes = self.modelo.getHistorialMensajesConsumo(idHilo)
        #return json.load(mensajes)
        hmensajes = [m['datos'] for m in mensajes]
        return hmensajes
    
    def getHistorialMensajes2(self, idHilo):
        mensajes = self.modelo.getHistorialMensajes2(idHilo)
        #return json.load(mensajes)
        hmensajes = [m['datos'] for m in mensajes]
        return hmensajes

    def crearHilo(self):
        idHilo = self.modelo.getIdHilo()
        return idHilo

    def probarConexion(self):
        return self.modelo.probarConexion()