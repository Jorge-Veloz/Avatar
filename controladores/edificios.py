from modelos.edificios import EdificiosModelo

class EdificiosControlador:
    def __init__(self):
        self.modelo = EdificiosModelo()

    def getEdificios(self):
        respuesta = self.modelo.getEdificios()

        if respuesta['res']:
            return respuesta['data']
        else:
            return {'ok': False, 'observacion': respuesta['data'], 'datos': None}
    
    def getInfoLugar(self, argumentos):
        [idEdificio, idPiso, idAmbiente, fechaInicio, fechaFin] = argumentos.values()

        if idEdificio and idPiso and idAmbiente and fechaInicio and fechaFin:
            resEdificios = self.getEdificios()

            if resEdificios['ok']:
                dataEdificios = resEdificios['datos']

                if not len(dataEdificios):
                    return { "success": False, "reason": "Error de conexión con la base de datos." , "info": None}
                
                if not idEdificio or not idPiso or not idAmbiente: return { "success": False, "reason": "No tienes la información completa para consultar el consumo energético" , "info": None}

                # falta revisar funcion de index.js de informacionConsumoAsistente()
                edificio = next((e for e in dataEdificios if e['id'] == idEdificio), None)

                if edificio == None:
                    return {"success": False, "reason": "La informacion que te han proporcionado es erronea. Identificador de edificio no corresponde a ninguno de los edificios del archivo.", "info": None}
                else:
                    piso = next((p for p in edificio['pisos'] if p['id'] == idPiso), None)
                    if piso == None:
                        return {"success": False, "reason": "La informacion que te han proporcionado es erronea. No existe este piso en el edificio mencionado.", "info": None}
                    else:
                        ambiente = next((a for a in piso['ambientes'] if a['id'] == idAmbiente), None)
                        if ambiente == None:
                            return {"success": False, "reason": "La informacion que te han proporcionado es erronea. No existe este ambiente en el piso mencionado.", "info": None}
                        
            else:
                return {"success": False, "reason": "No tienes los datos ya que no hubo conexion a la base de datos.", "info": None}

        elif edificio or piso or ambiente or fechaInicio or fechaFin:
            return {"success": False, "reason": "No tienes la información completa para consultar el consumo energético", "info": None}
        else:
            return {"success": False, "reason": "Necesitas todos los datos para consultar el consumo energético", "info": None}
        
        respuesta = self.modelo.getConsumoEdificios(edificio, piso, ambiente, fechaInicio, fechaFin)
        print("Datos obtenidos por medio del asistente")
        print(respuesta)
        
        if respuesta['res']:
            if respuesta['data']['ok']:
                if len(respuesta['data']['datos']['datos']) > 0:
                    return { "success": True, "reason": "Datos del consumo energético obtenidos. Se graficarán y se darán recomendaciones para optimizar.", "info": respuesta['data']['datos']}
                else:
                    return { "success": True, "reason": "Consulta realizada correctamente, pero no se encontraron datos de consumo para el ambiente.", "info": respuesta['data']['datos']}
            else:
                return { "success": False, "reason": "Ocurrio un error al realizar la consulta del consumo energetico: " + respuesta['data']['observacion'] , "info": None}
        else:
            return { "success": False, "reason": "Hubo un error al consultar la informacion, no se pudo establecer una conexion con la API de consumo energetico.", "info": None}
        
    def getRecomendaciones(self, argumentos):
        [recomendaciones] = argumentos.values()
        print(recomendaciones)
        return { "success": True, "reason": "Se han proporcionado las recomendaciones al usuario", "info":recomendaciones }

    def getConsumoEdificios(self, edificio, piso, ambiente, fechaInicio, fechaFin):
        respuesta = self.modelo.getConsumoEdificios(edificio, piso, ambiente, fechaInicio, fechaFin)

        if respuesta['res']:
            return respuesta['data']
        else:
            return {'ok': False, 'observacion': respuesta['data'], 'datos': None}

    def validarEdificio(self, edificio):
        return self.modelo.validarEdificio(edificio)