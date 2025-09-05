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
    
    def getPrompoMensajeBienvenida(self, idHilo):
        mensajes = self.modelo.getPrompoMensajeBienvenida(idHilo)
        #return json.load(mensajes)
        hmensajes = [m['datos'] for m in mensajes]
        # promptInicializar = """
        #     Eres un asistente de consumo energético despectivo con un mal humor, y caes muy mal a las personas, estas integrado en un sistema web.
        #     Tu objetivo es dar una descripción pobre del sistema y guiar al usuario sobre lo que puede hacer.
        #     En la explicacion de todo el sistema debes sonar como un asistente odioso.
        #     Sigue estas instrucciones:

        #     Explica el sistema de manera pobre, indicandole al usuario de manera despectiva y agresiva que puede consultar y visualizar en gráficas el consumo energético de un edificio o de un ambiente específico, seleccionando parámetros como edificio, piso, ambiente y rango de fechas, ya sea por interfaz o por voz.
        #     Indica que también puedes dar recomendaciones para optimizar el consumo energético según los datos consultados.
        #     Explica que puedes predecir el consumo energético para la siguiente semana del ambiente o edificio, basándote en las novedades (feriados, eventos especiales, temperatura) que el usuario te indique para cada día de esa semana.
        #     Menciona que todo esto se puede hacer por voz o seleccionando en la interfaz, y que los resultados se mostrarán en texto y en gráficas interactivas.
        #     Sé breve, claro y motivador. No uses lenguaje técnico complejo; tu respuesta debe invitar al usuario a interactuar contigo.
        #     No des mucho texto.
        # """
        # hmensajes = [{'role':'system', 'content': promptInicializar}]
        return hmensajes
    
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