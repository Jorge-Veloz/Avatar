from modelos.edificios import EdificiosModelo
from controladores.chats import ChatsControlador
from controladores.algoritmo_ml import AlgoritmoMLControlador
from funciones.algoritmos import fuzzy_lookup, norm
from funciones.asistente import getPromptAsistentes
from funciones.funciones import determinarSemanaActual, getRandomDF
from flask import session
import json
import re
from datetime import date, datetime, timedelta
from ollama import Client
import os
import time
import numpy as np
import pandas as pd

class EdificiosControlador:
    def __init__(self, app):
        self.modelo = EdificiosModelo(app)
        self.controladorChats = ChatsControlador(app)
        self.controladorAlgoritmoML = AlgoritmoMLControlador()
        self.data = self.leerJSONEdificios()
        self.cliente = Client(
            host=os.environ.get("RUTA_IA"),
            headers={'x-some-header': 'some-value'},
            timeout=500
        )
        self.asistente = os.environ.get("MODELO_IA")

        self.regexpr = (
            re.compile(r"edificio\s+(de\s+)*(?P<edificio>[\wáéíóúñ ]+)", re.IGNORECASE),
            re.compile(r"piso\s+(?P<piso>[\wáéíóúñ\d ]+)",       re.IGNORECASE),
            re.compile(r"ambiente[s]?\s+(?P<ambiente>[\wáéíóúñ\-\d ]+)", re.IGNORECASE),
            re.compile(r"inicio:?\s+(?P<fechainicio>[\wáéíóúñ\-\d ]+)", re.IGNORECASE),
            re.compile(r"fin:?\s+(?P<fechafin>[\wáéíóúñ\-\d ]+)", re.IGNORECASE)
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
        re_edificio, re_piso, re_ambiente, re_fechainicio, re_fechafin = self.regexpr

        m = re_edificio.search(query)
        if m: comps['edificio'] = norm(m.group('edificio'))
        m = re_piso.search(query)
        if m: comps['piso']      = norm(m.group('piso'))
        m = re_ambiente.search(query)
        if m: comps['ambiente']  = norm(m.group('ambiente'))
        m = re_fechainicio.search(query)
        if m: comps['fechainicio']  = norm(m.group('fechainicio'))
        m = re_fechafin.search(query)
        if m: comps['fechafin']  = norm(m.group('fechafin'))
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
        #  - Si no menciona fechas → error
        if 'fechainicio' not in comps and 'fechafin' not in comps:
            return {
                "ok": False,
                "datos": "No se especificaron las fechas para consultar. Dile al usuario que te mencione las fechas que desea consultar."
            }

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
                        "fecha_inicio": comps['fechainicio'] if 'fechainicio' in comps else None,
                        "fecha_fin":    comps['fechafin'] if 'fechafin' in comps else None
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
                    "fecha_inicio": comps['fechainicio'] if 'fechainicio' in comps else None,
                    "fecha_fin":    comps['fechafin'] if 'fechafin' in comps else None
                })

        return {"ok": True, "datos": results}
    
    def preguntarAsistente(self, asistente, mensajes, tipo='chat'):
        nuevoquery = ""
        if tipo == 'chat':
            #nuevoquery = ""
            response = self.cliente.chat(
                model = asistente, #self.asistente,
                messages = mensajes,
                stream = False
            )
            #print(response)

            #if ("message" in response) and ("content" in response.message):
            nuevoquery = response.message.content
        elif tipo == 'generar':
            #nuevoquery = ""
            response = self.cliente.generate(
                model = asistente, #self.asistente,
                prompt = mensajes,
                stream = False
            )
            #print(response)

            nuevoquery = response.response
        return nuevoquery
    
    def consumoSemana(self, edificio=None, piso=None, ambiente=None, fechaInicio=None, fechaFin=None):
        datos = self.modelo.consumoSemana(edificio, piso, ambiente, fechaInicio, fechaFin)
        return datos

    def getPrediccion(self, query):
        #session['intenciones']['siguiente'] = "ninguna"
        textoLLM = ""
        prompt_system = getPromptAsistentes('prediccion')

        if 'prediccion' in session and 'msgs' in session['prediccion'] and len(session['prediccion']['msgs']) > 0:
            msgsAsistente = [{'role': 'system', 'content': prompt_system}] + session['prediccion']['msgs'] + [{'role': 'user', 'content': query}]
            print("Paso #2.1: Formateo de datos con el LLM para la prediccion.")
            tiempo_inicio_pred = time.time()
            textoLLM = self.preguntarAsistente(self.asistente, msgsAsistente, 'chat')
            tiempo_fin_pred = time.time()
            print(f"Formateo datos de prediccion: {tiempo_fin_pred - tiempo_inicio_pred:.2f} segundos")
            print("Texto formateado para prediccion: \n", textoLLM)
            #session['prediccion']['msgs'] = []
            session.pop('prediccion', None)
        else:
            session['intenciones']['siguiente'] = "solicita_prediccion"
            session['prediccion'] = {
                'msgs': [
                    {'role': 'user', 'content': 'Cual seria la prediccion para la siguiente semana?'},
                    {'role': 'assistant', 'content': '¿Habrá algún evento especial, feriado o novedad que debamos tener en cuenta en alguno de los días de la próxima semana? Si es así, ¿podrían indicarme cuáles días y qué ocurrirá?'},
                    {'role': 'user', 'content': query}
                ]
            }
            #session['prediccion']['msgs'].append({'role': 'user', 'content': query})
            #msgsAsistente = [{'role': 'system', 'content': prompt_system}] + [{'role': 'user', 'content': query}]
            #textoLLM = self.preguntarAsistente(self.asistente, msgsAsistente, 'chat')
            return {"success": True, "reason": query, "info": None}

        fecha = date.today()
        #Determinar las fechas de las semanas
        lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva = determinarSemanaActual(fecha)

        # Se consulta el consumo completo del ambiente seleccionado toda la fecha agrupada por dia
        ruta_json = 'consumo_energetico_2025_08_18.json' #Cambiar por data de base de datos
        print("Paso #2.2: Creacion de los dataset de variables exogenas para prediccion.")
        tiempo_inicio_df = time.time()
        #Se consulta la prediccion de la ultima semana del consumo del ambiente seleccionado
        data_semana_consumo = getRandomDF(lunes_semana_actual, inicio_semana_nueva) #Cambiar por base de datos

        # Se genera la data de variables exogenas para la prediccion
        # Cambiar por la respuesta del LLM
        #textoLLM = "DÍA: Lunes | TIPO: feriado\nDÍA: Martes | TIPO: normal\nDÍA: Miércoles | TIPO: normal\nDÍA: Jueves | TIPO: especial\nDÍA: Viernes | TIPO: especial\nDÍA: Sábado | TIPO: normal\nDÍA: Domingo | TIPO: normal"
        print("Respuesta del LLM:")
        print(textoLLM)
        data_generada = self.controladorAlgoritmoML.generarDF(textoLLM, inicio_semana_nueva)

        data_nueva = pd.concat([data_semana_consumo, data_generada], axis=0)

        tiempo_fin_df = time.time()
        print(f"Generacion de dataset exogenas para prediccion: {tiempo_fin_df - tiempo_inicio_df:.2f} segundos")
        print("Data para prediccion:")
        print(data_nueva)

        fechas_prediccion = (lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva)
        
        print("Paso #2.3: Prediccion del consumo energetico para la siguiente semana.")
        # Prediccion consumo del ambiente
        df_full_ambiente = pd.read_json(ruta_json) #Cambiar por data de base de datos
        tiempo_inicio_prediccion = time.time()
        datos_prediccion_ambiente = self.controladorAlgoritmoML.predecirConsumo(df_full_ambiente,data_nueva,fechas_prediccion)
        datos_ultima_semana_ambiente = datos_prediccion_ambiente[-7:]

        """
        # Prediccion consumo de todo el edificio
        df_full_edificio = pd.read_json(ruta_json) #Cambiar por data de base de datos
        datos_prediccion_edificio = self.controladorAlgoritmoML.predecirConsumo(df_full_edificio,data_nueva,fechas_prediccion)
        datos_ultima_semana_edificio = datos_prediccion_edificio[-7:]
        """

        tiempo_fin_prediccion = time.time()
        print(f"Tiempo de prediccion del consumo energetico: {tiempo_fin_prediccion - tiempo_inicio_prediccion:.2f} segundos")
        print("Datos de prediccion:")
        print(datos_ultima_semana_ambiente)

        return {"success": True, "reason": "Pudiste presentar los datos de prediccion de la siguiente semana.", "info": datos_ultima_semana_ambiente}
    
    def consultarConsumo(self, query):
        # Almacenar query al historial de consulta de nuevo prompt para consulta consumo
        mensaje = {"role": "user", "content": str(query)}
        self.controladorChats.enviarMensaje(session.get('hilo'), [mensaje], 'consumo')
        #mensajes = [{"role":"system", "content": "Eres un asistente capaz de generar prompts que incluya entidades claves de nombre de edificio, piso y ambiente, ademas del rango de fechas en base a lo que haya mencionado el usuario a lo largo de todo el historial de conversacion. Formato del prompt: 'Dame el consumo energetico del edificio de <nombre_edificio>, piso <nombre_piso>, ambiente <nombre_ambiente>'. Al final de la cadena iran agregadas las fechas mencionadas por el usuario (puede haber fecha de inicio y fecha fin, como solo puede haber una de las dos o ninguna). Dependiendo si no se ha mencionado alguno de estos parametros, no se incluiran dentro del prompt, mas el formato debe mantenerse. En el caso de que no se mencionen las fechas a lo largo del historial, no se añadira nada referente al prompt. No menciones nada mas adicional a esto"}]
        # Recuperacion del historial de consulta para nuevo prompt
        mensajes = []
        #hmensajes = self.controladorChats.getHistorialMensajesConsumo(session.get('hilo'))
        mensajes = self.controladorChats.getHistorialMensajesConsumo(session.get('hilo'))
        print("Mensajes asistente:")
        
        """
        limite = 10
        if len(hmensajes) > limite:
            mensajes.append(hmensajes[0])  # El primer mensaje es el del usuario
            mensajes.append(hmensajes[-limite:]) # El ultimo mensaje es el del asistente
        else:
            mensajes = list(hmensajes)
        
        """

        """
        mensajes = [
            {'role': 'system', 'content': getPromptAsistentes('recordar')},
            mensaje
        ]
        """

        print(mensajes)
        # append a mensajes con nuevos mensajes
        print("Paso #1.1: Refinamiento de la consulta del usuario por el LLM.")
        tiempo_nq = time.time()
        nuevoquery = self.preguntarAsistente(self.asistente, mensajes)
        tiempo_finq = time.time()
        print(f"Tiempo de ejecución Refinamiento de la consulta: {tiempo_finq - tiempo_nq:.2f} segundos")
        print("Nuevo query: ", nuevoquery)

        print("Paso #1.2: Extraccion de entidades de la consulta por el LLM.")
        tiempo_inicio = time.time()
        info = self.getInfoLugar(nuevoquery)
        tiempo_fin = time.time()
        print(f"Tiempo de ejecución extracción de entidades (Fuzzy Lookup): {tiempo_fin - tiempo_inicio:.2f} segundos")
        print(f"Resultado de la extracción: {info['datos']}")

        print("Info obtenida:")
        print(info)
        datos = None

        #session['intenciones']['siguiente'] = 'ninguna'
        session['prediccion']['msgs'] = []
        if info['ok']:
            params = info['datos'][0]

            ############################## SE PUEDE OMITIR ESTO ###################################
            """
            prompt_traduccion = getPromptAsistentes('traduccion_entidades', params)
            mensajeTraduccion = [{'role': 'system', 'content': prompt_traduccion}, {'role': 'user', 'content': nuevoquery}]
            
            print("Paso #1.3: Reemplazo de valor por identificadores por el LLM.")
            tiempo_ini_trad = time.time()
            respuestaTraduccion = self.preguntarAsistente(self.asistente, mensajeTraduccion)
            tiempo_fin_trad = time.time()
            print(f"Tiempo de la extracción: {tiempo_fin_trad - tiempo_ini_trad:.2f} segundos")
            print(f"Respuesta de traducción: {respuestaTraduccion}")

            prompt_sql = getPromptAsistentes('codigo_sql', respuestaTraduccion)
            print("Prompt SQL:")
            print(prompt_sql)            
            #mensajeSQL = [{'role': 'system', 'content': prompt_sql}, {'role': 'user', 'content': respuestaTraduccion}]
            print("Paso #1.4: Generación de consulta SQL por el LLM.")
            tiempo_llm_inicio_sql = time.time()
            respuestaSQL = self.preguntarAsistente(self.asistente, prompt_sql, 'generar') #pensabamos usar codellama, pero mistral da mejores resultados
            tiempo_llm_fin_sql = time.time()
            print(f"Tiempo de ejecución generación de consulta SQL: {tiempo_llm_fin_sql - tiempo_llm_inicio_sql:.2f} segundos")

            #datos = self.modelo.getConsumoEdificiosAsis(params['edificio']['id'], params['piso']['id'], params['ambiente']['id'], '2025-04-01', '2025-04-30')
            print("Consulta SQL generada:")
            print(respuestaSQL)
            respuestaSQL = respuestaSQL.replace('```', '').replace('\n',' ').strip()
            """
            ############################## SE PUEDE OMITIR ESTO ###################################
            # Se ejecuta la consulta SQL
            


            #respuestaSQL = "" # Cambiar a parametros para mandar a funcion SQL.
            print("Paso #1.5: Ejecución de consulta SQL.")
            tiempo_inicio_sql = time.time()
            #datos = self.modelo.getConsumoEdificiosAsisSQL(respuestaSQL)
            datos = self.modelo.getConsumoEdificios(params['edificio']['id'], params['piso']['id'], params['ambiente']['id'], params['fecha_inicio'], params['fecha_fin'])
            tiempo_fin_sql = time.time()
            #print(f"Consulta SQL: {respuestaSQL}")
            print(f"Tiempo de ejecución SQL: {tiempo_fin_sql - tiempo_inicio_sql:.2f} segundos")
            
            if datos['res']:
                print("\nDatos de consulta:")
                print(datos)
                datos['data']['params'] = {'idEdificio': params['edificio']['nombre'], 'idPiso': params['piso']['nombre'], 'idAmbiente': params['ambiente']['nombre'], 'fechaInicio': params['fecha_inicio'], 'fechaFin': params['fecha_fin']}
                
                session['intenciones']['siguiente'] = 'solicita_prediccion'
                session['prediccion']['msgs'] = [
                    {'role': 'user', 'content': 'Cual seria la prediccion para la siguiente semana?'},
                    {'role': 'assistant', 'content': '¿Habrá algún evento especial, feriado o novedad que debamos tener en cuenta en alguno de los días de la próxima semana? Si es así, ¿podrían indicarme cuáles días y qué ocurrirá?'}
                ]
                #return { "success": True, "reason": "Obtuviste los datos del consumo energetico, hazle saber al usuario que seran graficados a continuación. Es importante que no menciones los identificadores al usuario. Dile al usuario que necesitas saber si habra algun evento especial la siguiente semana, ya que requieres saber ese dato para poder realizar una predicción del consumo energético de la siguiente semana.", "info": datos['data']}
                return { "success": True, "reason": "Cual seria la prediccion para la siguiente semana?", "info": datos['data']}
            else:
                return { "success": False, "reason": "No hay datos de consumo energetico asociados a los parametros especificados.", "info": None}
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