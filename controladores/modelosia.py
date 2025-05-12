from modelos.modelosia import IAModelo

class IAControlador:
    def __init__(self):
        self.categorias = {
            "solicita_datos_consumo": self.get_consumo
        }
        etiquetas = list(self.categorias.keys())
        self.modelo = IAModelo(etiquetas)
    
    def detectar_intencion(self, consulta, etiquetas):
        resultado = self.modelo.detectar_intencion(consulta, etiquetas)
        return resultado['intencion']
        
        if resultado['intencion'] in self.categorias:
            funcion = self.categorias[resultado['intencion']]
            return funcion()

    def get_consumo(self):
        pass

