from modelos.edificios import EdificiosModelo
from controladores.chats import ChatsControlador
from funciones.algoritmos import fuzzy_lookup, norm
from funciones.asistente import getPromptAsistentes
from flask import session
import json
import re
#from unidecode import unidecode
from datetime import date
from ollama import Client
import os

class EdificiosControlador:
    def __init__(self, app):
        self.modelo = EdificiosModelo(app)
        self.controladorChats = ChatsControlador(app)
        self.data = self.leerJSONEdificios()
        self.cliente = Client(
            host=os.environ.get("RUTA_IA"),
            headers={'x-some-header': 'some-value'}
        )
        self.asistente = os.environ.get("MODELO_IA")

        self.regexpr = (
            re.compile(r"edificio\s+(de\s+)*(?P<edificio>[\wáéíóúñ ]+)", re.IGNORECASE),
            re.compile(r"piso\s+(?P<piso>[\wáéíóúñ\d ]+)",       re.IGNORECASE),
            re.compile(r"ambiente\s+(?P<ambiente>[\wáéíóúñ\-\d ]+)", re.IGNORECASE)
        )

    
    def extraer_fechas_iso(self, query: str):
        
        # ——————————————————————————————————————————
        # Extracción de fechas en formato ISO YYYY-MM-DD
        # ——————————————————————————————————————————
        ISO_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

        found = ISO_DATE_RE.findall(query)

        if not found:
            return None, None
        fi = date.fromisoformat(found[0])
        ff = date.fromisoformat(found[1]) if len(found) > 1 else fi
        return fi, ff
        
    def leerJSONEdificios(self):
        ruta = 'data_edificios2.json'
        with open(ruta, 'r', encoding='utf-8') as f:
            return json.load(f)  # data es una lista de dicts

    def getEdificios(self):
        respuesta = self.modelo.getEdificios()

        if respuesta['res']:
            return respuesta['data']
        else:
            return {'ok': False, 'observacion': respuesta['data'], 'datos': None}

    def extract_components(self, query: str):
        comps = {}
        re_edificio, re_piso, re_ambiente = self.regexpr

        m = re_edificio.search(query)
        if m: comps['edificio'] = norm(m.group('edificio'))
        m = re_piso.search(query)
        if m: comps['piso']      = norm(m.group('piso'))
        m = re_ambiente.search(query)
        if m: comps['ambiente']  = norm(m.group('ambiente'))
        return comps
    
    def getInfoLugar(self, query):
        
        # 1) Extraer fechas ISO
        # fecha_inicio, fecha_fin = self.extraer_fechas_iso(query)
        # if not fecha_inicio:
        #     return {"ok": False, "datos": "No encontré fechas en formato YYYY-MM-DD en la consulta."}
        
        comps = self.extract_components(query)
        # Validación de extracción
        if not comps:
            #return {"ok": False, "datos": "No pude extraer edificio, piso ni ambiente de la consulta."}
            return {"ok": False, "datos": "No pudiste reconocer el edificio, piso ni ambiente de la peticion del usuario."}

        # Validaciones de contexto
        #  - Si pide solo piso sin edificio → error
        if 'piso' in comps and 'edificio' not in comps:
            return {
                "ok": False,
                "datos": "Te solicitaron un piso pero no especificaron edificio; al haber varios pisos en distintos edificios, no puedes filtrar. Dile al usuario que te diga el edificio que desea consultar."
            }
        #  - Si pide solo ambiente sin piso ni edificio → error
        if 'ambiente' in comps and ('piso' not in comps or 'edificio' not in comps):
            return {
                "ok": False,
                "datos": "Te solicitaron un ambiente pero no especificaron piso y edificio; al haber múltiples ambientes en distintos pisos y edificios, no puedes filtrar. Dile al usuario que te diga el edificio y el piso que desea consultar."
            }

        # — 5.1 Filtrar edificios
        if 'edificio' in comps:
            ed = next((b for b in self.data if norm(b['nombre']) == comps['edificio']), None)
            if not ed:
                ed = fuzzy_lookup(comps['edificio'], self.data)
            if not ed:
                return {"ok": False, "datos": f"Edificio '{comps['edificio']}' no encontrado."}
            edificios = [ed]
        else:
            edificios = self.data

        # — 5.2 Filtrar pisos (solo si pide piso o ambiente)
        pisos_matches = []
        if 'piso' in comps:
            for b in edificios:
                p = next((p for p in b['pisos'] if norm(p['nombre']) == comps['piso']), None)
                if not p:
                    p = fuzzy_lookup(comps['piso'], b['pisos'])
                if p:
                    pisos_matches.append({"edificio": b, "piso": p})
            if not pisos_matches:
                return {"ok": False, "datos": f"El piso '{comps['piso']}' solicitado no fue encontrado en el edificio solicitado."}
        else:
            # si no pide piso, tomo todos los pisos de los edificios filtrados
            for b in edificios:
                for p in b['pisos']:
                    pisos_matches.append({"edificio": b, "piso": p})

        # — 5.3 Filtrar ambientes (solo si pide ambiente)
        results = []
        if 'ambiente' in comps:
            for item in pisos_matches:
                b, p = item['edificio'], item['piso']
                a = next((a for a in p['ambientes'] if norm(a['nombre']) == comps['ambiente']), None)
                if not a:
                    a = fuzzy_lookup(comps['ambiente'], p['ambientes'])
                if a:
                    results.append({
                        "edificio":     {"id": b['id'],   "nombre": b['nombre']},
                        "piso":         {"id": p['id'],   "nombre": p['nombre']},
                        "ambiente":     {"id": a['id'],   "nombre": a['nombre']},
                        # "fecha_inicio": fecha_inicio.isoformat(),
                        # "fecha_fin":    fecha_fin.isoformat()
                    })
            if not results:
                return {"ok": False, "datos": f"El ambiente '{comps['ambiente']}' solicitado no fue encontrado en el piso solicitado."}
        else:
            # si no pide ambiente, retorno cada piso (con su edificio)
            for item in pisos_matches:
                b, p = item['edificio'], item['piso']
                results.append({
                    "edificio":     {"id": b['id'],   "nombre": b['nombre']},
                    "piso":         {"id": p['id'],   "nombre": p['nombre']},
                    # "fecha_inicio": fecha_inicio.isoformat(),
                    # "fecha_fin":    fecha_fin.isoformat(),
                })

        return {"ok": True, "datos": results}
    
    def preguntarAsistente(self, asistente, mensajes):
        #nuevoquery = ""
        response = self.cliente.chat(
            model = asistente, #self.asistente,
            messages = mensajes,
            stream = False
        )
        #print(response)

        #if ("message" in response) and ("content" in response.message):
        nuevoquery = response.message.content

        return nuevoquery
    
    def consultarConsumo(self, query):
        # Almacenar query al historial de consulta de nuevo prompt para consulta consumo
        mensaje = {"role": "user", "content": str(query)}
        self.controladorChats.enviarMensaje(session.get('hilo'), [mensaje], 'consumo')
        #mensajes = [{"role":"system", "content": "Eres un asistente capaz de generar prompts que incluya entidades claves de nombre de edificio, piso y ambiente, ademas del rango de fechas en base a lo que haya mencionado el usuario a lo largo de todo el historial de conversacion. Formato del prompt: 'Dame el consumo energetico del edificio de <nombre_edificio>, piso <nombre_piso>, ambiente <nombre_ambiente>'. Al final de la cadena iran agregadas las fechas mencionadas por el usuario (puede haber fecha de inicio y fecha fin, como solo puede haber una de las dos o ninguna). Dependiendo si no se ha mencionado alguno de estos parametros, no se incluiran dentro del prompt, mas el formato debe mantenerse. En el caso de que no se mencionen las fechas a lo largo del historial, no se añadira nada referente al prompt. No menciones nada mas adicional a esto"}]
        # Recuperacion del historial de consulta para nuevo prompt
        #mensajes = []
        #hmensajes = self.controladorChats.getHistorialMensajesConsumo(session.get('hilo'))
        mensajes = self.controladorChats.getHistorialMensajesConsumo(session.get('hilo'))
        print("Mensajes asistente:")
        """
        mensajes.append(hmensajes[0])  # El primer mensaje es el del usuario
        mensajes.append(hmensajes[-1]) # El ultimo mensaje es el del asistente
        
        
        mensajes = [
            {'role': 'system', 'content': getPromptAsistentes('recordar')},
            mensaje
        ]
        """
        print(mensajes)
        # append a mensajes con nuevos mensajes
        nuevoquery = self.preguntarAsistente(self.asistente, mensajes)
        print("Nuevo query: ", nuevoquery)

        info = self.getInfoLugar(nuevoquery)
        print("Info obtenida:")
        print(info)
        datos = None

        if info['ok']:
            params = info['datos'][0]
            prompt_traduccion = getPromptAsistentes('traduccion_entidades', params)
            mensajeTraduccion = [{'role': 'system', 'content': prompt_traduccion}, {'role': 'user', 'content': nuevoquery}]
            respuestaTraduccion = self.preguntarAsistente(self.asistente, mensajeTraduccion)
            print("Respuesta de traducción:")
            print(respuestaTraduccion)

            prompt_sql = getPromptAsistentes('codigo_sql')
            mensajeSQL = [{'role': 'system', 'content': prompt_sql}, {'role': 'user', 'content': respuestaTraduccion}]
            respuestaSQL = self.preguntarAsistente(self.asistente, mensajeSQL) #pensabamos usar codellama, pero mistral da mejores resultados

            #datos = self.modelo.getConsumoEdificiosAsis(params['edificio']['id'], params['piso']['id'], params['ambiente']['id'], '2025-04-01', '2025-04-30')
            print("Consulta SQL generada:")
            print(respuestaSQL)
            respuestaSQL = respuestaSQL.replace('```', '').replace('\n',' ').strip()

            datos = self.modelo.getConsumoEdificiosAsisSQL(respuestaSQL)
            if datos['res']:
                print("\nDatos de consulta:")
                print(datos)
                datos['data']['params'] = {'idEdificio': params['edificio']['nombre'], 'idPiso': params['piso']['nombre'], 'idAmbiente': params['ambiente']['nombre'], 'fechaInicio': '2025-04-01', 'fechaFin': '2025-04-30'}
                #session['memoria']['consumo'] = datos['data']['params']
                return { "success": True, "reason": "Obtuviste los datos del consumo energetico, hazle saber al usuario que seran graficados a continuación. Es importante que no menciones los identificadores al usuario. Dile al usuario que necesitas saber si habra algun evento especial la siguiente semana, ya que requieres saber ese dato para poder realizar una predicción del consumo energético de la siguiente semana.", "info": datos['data']}
            else:
                return { "success": True, "reason": "No hay datos de consumo energetico asociados a los parametros especificados.", "info": None}
        else:
            return {"success": False, "reason": info['datos'], "info": None}


    def getInfoLugarAnt(self, argumentos):
        pObl = ['edificio', 'piso', 'ambiente', 'fechaIni', 'fechaFin']

        for p in pObl:
            if p not in argumentos.keys():
                return { "success": False, "reason": "No tienes la información completa para consultar el consumo energético", "info": None}    
        
        idEdificio = argumentos['edificio']
        idPiso = argumentos['piso']
        idAmbiente = argumentos['ambiente']
        fechaInicio = argumentos['fechaIni']
        fechaFin = argumentos['fechaFin']

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

        elif idEdificio or idPiso or idAmbiente or fechaInicio or fechaFin:
            return {"success": False, "reason": "No tienes la información completa para consultar el consumo energético", "info": None}
        else:
            return {"success": False, "reason": "Necesitas todos los datos para consultar el consumo energético", "info": None}

        #[idEdificio, idPiso, idAmbiente, fechaInicio, fechaFin] = argumentos.values()

        res = self.modelo.getConsumoEdificiosAsis(idEdificio, idPiso, idAmbiente, fechaInicio, fechaFin)

        if res['res']:
            res['data']['params'] = {'idEdificio': idEdificio, 'idPiso': idPiso, 'idAmbiente': idAmbiente, 'fechaInicio': fechaInicio, 'fechaFin': fechaFin}
            return { "success": True, "reason": "Obtuviste los datos del consumo energetico, hazle saber al usuario que seran graficados a continuación. Además dale unas recomendaciones para optimizar el consumo energetico del edificio y ambientes. Es importante que no menciones los identificadores al usuario.", "info": res['data']}
    
    def getInfoLugarGPT(self, argumentos):
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

        elif idEdificio or idPiso or idAmbiente or fechaInicio or fechaFin:
            return {"success": False, "reason": "No tienes la información completa para consultar el consumo energético", "info": None}
        else:
            return {"success": False, "reason": "Necesitas todos los datos para consultar el consumo energético", "info": None}
        
        respuesta = self.modelo.getConsumoEdificios(idEdificio, idPiso, idAmbiente, fechaInicio, fechaFin)
        #print("Datos obtenidos por medio del asistente")
        #print(respuesta)

        if respuesta['res']:
            if respuesta['data']['ok']:
                respuesta['data']['params'] = {'idEdificio': idEdificio, 'idPiso': idPiso, 'idAmbiente': idAmbiente, 'fechaInicio': fechaInicio, 'fechaFin': fechaFin}
                if len(respuesta['data']['datos']['datos']) > 0:
                    return { "success": True, "reason": "Obtuviste los datos del consumo energetico, hazle saber al usuario que seran graficados a continuación. Además dale unas recomendaciones para optimizar el consumo energetico del edificio y ambientes. Es importante que no menciones los identificadores al usuario.", "info": respuesta['data']}
                else:
                    return { "success": True, "reason": "Se realizo correctamente la consulta pero no habian datos de consumo de ese ambiente, hazle saber al usuario", "info": respuesta['data']}
            else:
                return { "success": False, "reason": "Los datos enviados fueron correctos, mas hubo un error a la consulta en la bd. Se trata del error: " + respuesta['data']['observacion'] , "info": None}
        else:
            return { "success": False, "reason": "Hubo un error al consultar la informacion, no se pudo establecer una conexion con la API de consumo energetico.", "info": None}
        
    def getRecomendaciones(self, query):
        response = self.cliente.generate(
            model = self.asistente, #self.asistente,
            #messages = list(session.get('hilo')['mensajes']),
            prompt = query,
            stream = False
        )

        recomendaciones = response['response']
        return { "success": True, "reason": "Diste correctamente las recomendaciones para optimizar el consumo energetico. Ahora mencionaselo al usuario.", "info":recomendaciones }
    
    def getRecomendacionesAnt(self, argumentos):
        if "recomendaciones" not in argumentos:
            return { "success": False, "reason": "No diste las recomendaciones al usuario. Vuelve a generar las recomendaciones.", "info": None}
        
        [recomendaciones] = argumentos.values()
        print("Recomendaciones obtenidas:")
        print(recomendaciones)
        #return { "success": True, "reason": "Informale al usuario que se ha porporcionado la informacion sobre las recomendaciones", "info":recomendaciones }
        return { "success": True, "reason": "Diste correctamente las recomendaciones para optimizar el consumo energetico. Ahora mencionaselo al usuario.", "info":recomendaciones }

    def getConsumoEdificios(self, edificio, piso, ambiente, fechaInicio, fechaFin):
        respuesta = self.modelo.getConsumoEdificios(edificio, piso, ambiente, fechaInicio, fechaFin)

        if respuesta['res']:
            return respuesta['data']
        else:
            return {'ok': False, 'observacion': respuesta['data'], 'datos': None}

    def validarEdificio(self, edificio):
        return self.modelo.validarEdificio(edificio)