from modelos.edificios import EdificiosModelo

class EdificiosControlador:
    def __init__(self):
        self.modelo = EdificiosModelo()

    def getEdificios(self):
        datos = self.modelo.getEdificios();

        if datos:
            return {'res': 1, 'datos': datos}
        else:
            return {'res': 0}
        
    def validarEdificio(self, edificio):
        return self.modelo.validarEdificio(edificio)