from modelos.ambiente import AmbientesModelo

class AmbientesControlador:
    def __init__(self):
        self.modelo = AmbientesModelo()

    def getAmbientes(self, edificio):
        datos = self.modelo.getAmbientes(edificio);

        if datos:
            return {'res': 1, 'datos': datos}
        else:
            return {'res': 0}