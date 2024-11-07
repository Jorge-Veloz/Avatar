from modelos.consumo import ConsumoModelo

class ConsumoControlador:
    def __init__(self):
        self.modelo = ConsumoModelo()

    def getConsumoActual(self, edificio, ambiente, fecha):
        res = {'res': 0}
        consumoEdificio = self.modelo.getConsumoActualTotal(edificio, fecha);

        if consumoEdificio:
            res['res'] = 1
            consumoAmbiente = self.modelo.getConsumoActual(edificio, ambiente, fecha)
            res['datos'] = {'consumo_actual_total': consumoEdificio, 'consumo_actual': consumoAmbiente}

        return res
    
    def getConsumoFuturo(self, datosConsumo):
        consumoAmbiente = self.modelo.getConsumoFuturo(datosConsumo['consumo_actual'])
        consumoEdificio = self.modelo.getConsumoFuturo(datosConsumo['consumo_actual_total'])

        return {
            'res': 1,
            'datos': {
                'consumo_futuro_total': consumoEdificio, 
                'consumo_futuro': consumoAmbiente
            }
        }