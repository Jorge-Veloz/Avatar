from flask import Flask, Response, render_template, url_for, request, session, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from controladores.asistente import AsistenteControlador
from controladores.edificios import EdificiosControlador
from controladores.ambientes import AmbientesControlador
from controladores.chats import ChatsControlador
from controladores.consumo import ConsumoControlador
from controladores.algoritmo_ml import AlgoritmoMLControlador
#from controladores.tts import TTSControlador
#from controladores.modelosia import IAControlador
#from controladores.speech import SpeechController
from funciones.asistente import getMensajeSistema, getPromptAsistentes
from funciones.algoritmos import getPrediccionConsumo, detectar_intencion, getPrediccionConsumoAnt
from funciones.funciones import determinarSemanaActual, getRandomDF
import pandas as pd
#from config import Config
#from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy.sql import text
import json
import os
import re
from dotenv import load_dotenv
import requests
import random
import string
from io import BytesIO
import time

load_dotenv(os.path.join(os.getcwd(), '.env'))

# Guardara todos los ChatCompletions de respuesta a las funciones del asistente
# Esto evita que el asistente vuelva a repetir el envio de la funcion
compMsgs = []
API_DB = os.environ.get("API_DB")
rutaGrabacion = "./static/media/records"

#speechController = SpeechController()

app = Flask(__name__)
app.config['SECRET_KEY'] = b'secret_key'
app.config['ASSETS_FOLDER'] = os.path.join(os.getcwd(), 'assets')

#Descomentar para conectar a la base de datos
controladorChats = ChatsControlador(app)

#print(controladorChats.enviarMensaje(1, {"role":"user", "content": "El usuario se ha conectado, preséntate ante el usuario y dale una bienvenida."}))
controladorAsistente = AsistenteControlador(app)
controladorEdificios = EdificiosControlador(app)
controladorAlgoritmoML = AlgoritmoMLControlador()
#controladorTTS = TTSControlador()
#controladorIA = IAControlador()

# Inicializacion del JWT
jwt = JWTManager(app)
 
with app.test_request_context():
    url_for('static', filename='/resources/')
    url_for('static', filename='/css/')
    url_for('static', filename='/scripts/')
    url_for('static', filename='/assets/')

# Ruta para servir archivos de la carpeta "assets"
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(app.config['ASSETS_FOLDER'], filename)

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('static', filename)

@app.get('/')
def Index():
    #if 'intenciones' in session:
    #    session.pop('intenciones', None)
    #if 'prediccion' in session:
    #    session.pop('prediccion', None)
    return render_template('index.html')

@app.get('/assistant')
def assistant():
    return render_template('assistant.html')

@app.post('/assistant/talk')
def assistant_talk():
    # Speech to text
    id = controladorAsistente.crearHilo()
    # text = speechController.speechToText(request.files['voice'], id)

    # With API
    ruta = f'{rutaGrabacion}/input-{id}.mp3'
    
    request.files['voice'].save(ruta)
    response = requests.post(
        url=os.environ.get("RUTA_VOZ")+'/voz_texto',
        files={'voice': ('voice.mp3', open(f'{rutaGrabacion}/input-{id}.mp3', 'rb'))},
        data={'id': id},
        verify=False
    )
    #response = requests.get(
    #    os.environ.get("RUTA_VOZ")+'/prueba'
    #    #files={'voice': ('voice.mp3', open(ruta, 'rb'))},
    #    #data={'id': id}
    #)
    text = response.json()['datos']
    #text = response.json()
    if not text.strip():
        text = 'No pude entender lo que dijiste, Podrías repetirlo porfavor?'
    print(text)
    
    mensajeAsistente = {"role":"user", "content": text}
    respuesta = controladorAsistente.getRespuesta(id, mensajeAsistente)
    session['contenido'] = []
    resultado = procesamientoConversacion(respuesta['datos'])
    #print("Texto obtenido: " + text)
    #return jsonify({'text': text})

    # Text to speech
    # With Controller
    # encoded = speechController.textToSpeech(text, id)
    # With API
    response1 = requests.post(
        url=os.environ.get("RUTA_VOZ")+'/texto_voz',
        data={'texto': resultado['datos']['respuesta'], 'id': id},
        verify=False
    )

    # tts = response1.json()
    # print(tts)
    # return jsonify({'tts': tts})
    encoded = response1.json()['datos']['voice_encoded']
    return {
        'text': text,
        'audio': encoded
    }

@app.get('/avatar')
def modeloAvatar():
    return render_template('avatar.html')

@app.get('/edificios')
def getEdificios():
    respuesta = controladorEdificios.getEdificios()
    estado = 200 if respuesta['ok'] else 500
    return jsonify(respuesta), estado

@app.get('/pruebaChats')
def pruebaChats():
    if 'hilo' not in session:
        hilo = controladorAsistente.crearHilo()
        session['hilo'] = hilo
    mensaje = controladorAsistente.getListaMensajes(session.get('hilo'))
    #mensaje = {"res": 1}
    return jsonify(mensaje)

@app.post('/reaccionar-msg')
def reaccionarMsg():
    if 'hilo' not in session:
        hilo = controladorAsistente.crearHilo()
        session['hilo'] = hilo
    json_string = request.data.decode('utf-8')
    data_dict = json.loads(json_string)

    idMensaje = data_dict['idMensaje']
    reaccion = data_dict['reaccion']
    
    resultado = controladorAsistente.reaccionarMensaje(session.get('hilo'), idMensaje, reaccion)
    #mensaje = {"res": 1}
    return jsonify(resultado)

@app.get('/pruebachat')
def pruebaChat():
    respuesta = controladorChats.getHistorialMensajesConsumo(1)
    return jsonify(respuesta)

@app.get('/datos')
def getConsumoEdificios():
    edificio = request.args.get('idEdificacion')
    piso = request.args.get('idPiso')
    ambiente = request.args.get('idAmbiente')
    fechaInicio = request.args.get('fechaInicio')
    fechaFin = request.args.get('fechaFin')

    respuesta = controladorEdificios.getConsumoEdificios(edificio, piso, ambiente, fechaInicio, fechaFin)
    return jsonify(respuesta)

@app.get('/inicializar')
def inicializarAsistente():
    if 'hilo' in session: session.pop('hilo')
    if 'contenido' in session: session.pop('contenido')
    if 'intenciones' in session: session.pop('intenciones')
    if 'prediccion' in session: session.pop('prediccion')
    if 'memoria' in session: session.pop('memoria')
    
    hilo = controladorAsistente.crearHilo()
    
    session['hilo'] = hilo
    mensajeInicial = {"role":"user", "content": "El usuario se ha conectado, preséntate ante el usuario y dale una bienvenida."}
    respuesta = controladorAsistente.getRespuesta(session.get('hilo'), [mensajeInicial], "inicializar") #enviar el identificador para obtener historial
    session['contenido'] = []
    #resultado = procesamientoConversacion(respuesta['datos'])

    # With API
    
    #response1 = controladorTTS.TextToSpeech(respuesta['datos'], session.get('hilo'))

    resultado = {
        'ok': True,
        'observacion': None,
        'datos': {"respuesta": respuesta['datos'], "info": session.get('contenido')}
    }

    response1 = requests.post(
        url=os.environ.get("RUTA_VOZ")+'/texto_voz',
        data={'texto': resultado['datos']['respuesta'], 'id': session.get('hilo')},
        verify=False
    )

    #encoded = response1['datos']['voice_encoded']
    encoded = response1.json()['datos']['voice_encoded']
    resultado['datos']['audio'] = encoded
    
    return jsonify(resultado)

@app.post('/inicializar_real_time')
def inicializarAsistenteRealTime():

    if 'hilo' in session: session.pop('hilo')
    if 'contenido' in session: session.pop('contenido')
    if 'intenciones' in session: session.pop('intenciones')
    if 'prediccion' in session: session.pop('prediccion')
    if 'memoria' in session: session.pop('memoria')
    
    hilo = controladorAsistente.crearHilo()
    
    session['hilo'] = hilo
    session['contenido'] = []
    
    # Genera el primer mensaje de bienvenida
    mensajes = [{"role": "user", "content": "El usuario se ha conectado, preséntate ante el usuario y dale una bienvenida.", "ok": True}]
    intenciones = {'anterior': 'ninguna', 'actual': 'ninguna', 'siguiente': 'ninguna'}
    def event_stream():
        txt_completo = ''
        buffer = ''
        for token in controladorAsistente.stream_tokens(hilo, "inicializar", mensajes, intenciones):
        # for token in llm_service.stream_tokens(prompt, model):
            # Enviar token
            yield f"{json.dumps({'type':'token','token':token})}\n\n"
            buffer += token
            txt_completo += token
            # Detectar oraciones completas
            parts = re.split(r'(?<=[.!?])\s+', buffer)
            if len(parts) > 1:
                for sent in parts[:-1]:
                    sent = sent.strip()
                    if sent:
                        audio = controladorAsistente.text_to_speech(sent)
                        yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
                buffer = parts[-1]
        # Última parte
        if buffer.strip():
            audio = controladorAsistente.text_to_speech(buffer)
            yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
        print("Guardar en la base de datos el mensaje completo:")
        controladorChats.enviarMensaje(hilo, [{"role": "assistant", "content": txt_completo}])
        yield "{\"type\":\"end\"}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')


@app.get('/api/prediccion')
def getPrediccion2():
    edificio = request.args.get('edificio')
    piso = request.args.get('piso')
    ambiente = request.args.get('ambiente')
    fecha = request.args.get('fecha')

    #Determinar las fechas de las semanas
    lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva = determinarSemanaActual(fecha)

    # Se consulta el consumo completo del ambiente seleccionado toda la fecha agrupada por dia
    ruta_json = 'consumo_energetico_2025_08_18.json' #Cambiar por data de base de datos

    #Se consulta la prediccion de la ultima semana del consumo del ambiente seleccionado
    data_semana_consumo = getRandomDF(lunes_semana_actual, inicio_semana_nueva) #Cambiar por base de datos

    # Se genera la data de variables exogenas para la prediccion
    # Cambiar por la respuesta del LLM
    textoLLM = "DÍA: Lunes | TIPO: feriado\nDÍA: Martes | TIPO: normal\nDÍA: Miércoles | TIPO: normal\nDÍA: Jueves | TIPO: especial\nDÍA: Viernes | TIPO: especial\nDÍA: Sábado | TIPO: normal\nDÍA: Domingo | TIPO: normal"
    
    data_generada = controladorAlgoritmoML.generarDF(textoLLM, inicio_semana_nueva)

    data_nueva = pd.concat([data_semana_consumo, data_generada], axis=0)

    fechas_prediccion = (lunes_semana_actual, domingo_semana_siguiente, inicio_semana_nueva)
    datos_prediccion = controladorAlgoritmoML.predecirConsumo(ruta_json,data_nueva,fechas_prediccion)

    datos_ultima_semana = datos_prediccion[-7:]

    return jsonify({'ok': True, 'observacion': None, 'datos': datos_ultima_semana})

@app.post('/conversar')
def getRespuesta():
    
    if 'hilo' not in session:
        session['hilo'] = controladorAsistente.crearHilo()

    if 'prediccion' not in session:
        session['prediccion'] = {'msgs': []}

    #if 'intenciones' not in session:
    #    session['intenciones'] = {'actual': 'ninguna', 'siguiente': 'ninguna'}
    if 'intenciones' in session: 
        print("Intenciones al inicio de la consulta: ")
        print(session['intenciones'])

    if 'intenciones' in session and 'actual' in session['intenciones']:
        session['intenciones']['anterior'] = session['intenciones']['actual']
    else:
        session['intenciones'] = {}
        session['intenciones']['anterior'] = 'ninguna'

    #session['intenciones'] = {'actual': 'ninguna', 'siguiente': 'ninguna'}
    session['intenciones']['actual'] = 'ninguna'
    session['intenciones']['siguiente'] = 'ninguna'

    codigo = session['hilo']
    intencion = request.form.get('intencion')
    print(f"Intención recibida: {intencion}")
    voz = request.files.get('voice')

    print("Paso #1: Conversión de voz a texto.")
    tiempo_inicio = time.time()
    sttRespuesta = controladorAsistente.speech_to_text(voz, codigo)
    tiempo_fin = time.time()
    print(f"Tiempo de ejecución Conversión de voz a texto: {tiempo_fin - tiempo_inicio:.2f} segundos")
    
    
    if sttRespuesta['ok']:
        textStt = sttRespuesta['datos']
    else:
        textStt = 'No pude entender lo que dijiste, Podrías repetirlo porfavor?'

    controladorChats.enviarMensaje(codigo, [{"role": "user", "content": textStt}])
    respuesta = procesamientoConversacion(textStt, intencion)
    
    print("Paso #1:")
    print("-----315------")
    print(respuesta)
    print("-----315------")
    #return session.get('contenido')
    print("-----319------")
    print(session.get('contenido'))
    print("-----319------")
    
    # PREPARACIÓN DE LOS DATOS PARA GRAFICOS
    print("-----324------")
    contenido = session.get('contenido', [])
    print(contenido)
    intenciones = session.get('intenciones', [])
    print("Intenciones antes de la respuesta:")
    print(session.get('intenciones', []))
    print("-----324------")
    
    def event_stream():
        
        buffer = ''
        txt_completo = ''
        
        if contenido:  # solo si hay datos
            yield f"{json.dumps({'type':'grafico','data': json.dumps(contenido, default=str)})}\n\n"

        if intenciones:  # solo si hay datos
            yield f"{json.dumps({'type':'intenciones','data': json.dumps(intenciones, default=str)})}\n\n"
        
        for token in controladorAsistente.stream_tokens(codigo, "conversar", respuesta, intenciones, contenido):
            # Enviar token
            yield f"{json.dumps({'type':'token','token':token})}\n\n"
            buffer += token
            txt_completo += token
            # Detectar oraciones completas
            parts = re.split(r'(?<=[.!?])\s+', buffer)
            if len(parts) > 1:
                for sent in parts[:-1]:
                    sent = sent.strip()
                    if sent:
                        audio = controladorAsistente.text_to_speech(sent)
                        yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
                buffer = parts[-1]
        # Última parte
        if buffer.strip():
            audio = controladorAsistente.text_to_speech(buffer)
            yield f"{json.dumps({'type':'audio','format':'wav','data':audio})}\n\n"
        print("Guardar en la base de datos el mensaje completo:")
        controladorChats.enviarMensaje(codigo, [{"role": "assistant", "content": txt_completo}])

        yield "{\"type\":\"end\"}\n\n"
    return Response(event_stream(), mimetype='text/event-stream')
    

    # resultado = {
    #     'ok': True,
    #     'observacion': None,
    #     'datos': {"respuesta": respuesta['datos'], "info": session.get('contenido')}
    # }

    # #response1 = controladorTTS.TextToSpeech(respuesta['datos'], codigo)
    # response1 = requests.post(
    #     url=os.environ.get("RUTA_VOZ")+'/texto_voz',
    #     data={'texto': resultado['datos']['respuesta'], 'id': session.get('hilo')},
    #     verify=False
    # )

    # #encoded = response1['datos']['voice_encoded']
    # respuesta_voz = response1.json()
    
    # encoded = respuesta_voz['datos']['voice_encoded']
    # resultado['datos']['audio'] = encoded

    # return jsonify(resultado)

@app.post('/conversarGPT')
def getRespuestaGPT():
    mensaje = request.form['mensaje']
    if 'idHilo' not in session:
        session['idHilo'] = controladorAsistente.obtenerIdHilo()
    
    respuesta = controladorAsistente.getRespuesta(session.get('idHilo'), mensaje)
    session['contenido'] = []
    resultado = procesamientoConversacion(respuesta['datos'])
    
    #salida = controladorAsistente.conversar(respuesta)
    return jsonify(resultado)

def procesamientoConversacion(texto, intencion='ninguna'):
    if intencion == 'ninguna': session['contenido'] = []
    funciones = {
        #'solicita_recomendaciones': controladorEdificios.getRecomendaciones,
        'solicita_datos_consumo': controladorEdificios.consultarConsumo,
        'solicita_prediccion': controladorEdificios.getPrediccion
    }
    etiquetas = list(funciones.keys())
    etiquetas.append('pregunta_respuesta_general')
    resultado = ''

    if intencion == 'ninguna':
        intencion_asistente = controladorEdificios.preguntarAsistente('mistral:latest', getPromptAsistentes('detectar_intencion', texto), 'generar')
        resultado = {'intencion': intencion_asistente.replace('-', '').replace('\n', '').strip().lower(), 'confidence': 1.0}
    else:
        resultado = {'intencion': intencion, 'confidence': 1.0}

    #intencion_asistente = controladorEdificios.preguntarAsistente('mistral:latest', getPromptAsistentes('detectar_intencion', texto))
    #resultado = detectar_intencion(texto, etiquetas) if intencion == 'ninguna' else {'intencion': intencion, 'confidence': 1.0}
    intencion =  'pregunta_respuesta_general' if resultado['intencion'] not in etiquetas else resultado['intencion']
    session['intenciones']['actual'] = str(intencion)

    mensajeAsistente = {"role": "user", "content": texto, "ok": True}
    mensajesAsis = [mensajeAsistente]
    
    if intencion != 'pregunta_respuesta_general':
        funcionIA = funciones[intencion]
        respuesta = funcionIA(texto)
        #mensajesAsis = [{"role": "user", "content": respuesta['reason'], "ok": respuesta['success']}]
        
        if respuesta['info']:
            session['contenido'].append({"nombre": intencion, "valor": respuesta['info']})
            mensajesAsis.append({"role": "user", "content": respuesta['reason'], "ok": respuesta['success']})
        else:
            mensajesAsis = [{"role": "user", "content": respuesta['reason'], "ok": respuesta['success']}]
        """else:
            #intencion = 'pregunta_respuesta_general'
            mensajesAsis = [{"role": "user", "content": respuesta['reason']}]"""
    #    return {"role": "user", "content": respuesta['reason']}
    #else:
    #    return None
    
    
    #if datos: mensajesAsis.append(datos)

    return mensajesAsis        

def procesamientoConversacionModelo(respuesta):
    print("Salida de la respuesta:")
    print(respuesta)
    if ('asis_funciones' in respuesta and respuesta['asis_funciones']):
        asisFunciones = respuesta['asis_funciones']
        funciones = {
            'is_get_consumo': controladorAsistente.verificarConsumo,
            'get_recomendaciones': controladorEdificios.getRecomendaciones,
            'get_parametros_edificio_piso_ambiente_fechas': controladorEdificios.getInfoLugar,
        }

        resFunciones = []
        for afuncion in asisFunciones: 
            if afuncion['funcion_name'] in funciones:
                func = funciones[afuncion['funcion_name']]
                rcontent = func(afuncion['funcion_args'])

                if rcontent['info']:
                    session['contenido'].append({"nombre": afuncion['funcion_name'], "valor": rcontent['info']})

                resFunciones.append({ "role": "tool", "name": afuncion['funcion_name'], "content": rcontent['reason'] })

        print(session.get('contenido'))
        print("Envio de funciones:")
        print(resFunciones)
        respuesta2 = controladorAsistente.enviarFunciones(session.get('hilo'), resFunciones)
        return procesamientoConversacion(respuesta2['datos'])
    elif ('respuesta_msg' in respuesta and respuesta['respuesta_msg']):
        return {
            'ok': True,
            'observacion': None,
            'datos': {"respuesta": respuesta['respuesta_msg'], "info": session.get('contenido')}
        }
    else:
        msgError = {"role": "user", "content": "No hubo respuesta por parte del asistente a la peticion previamente mencionada. Da una respuesta al usuario."}
        respuesta2 = controladorAsistente.getRespuesta(session.get('hilo'), msgError)
        return {
            'ok': True,
            'observacion': None,
            'datos':  {"respuesta": respuesta2['respuesta_msg'], "info": session.get('contenido')}
        }
    
def procesamientoConversacionGPT(respuesta):
    print("Salida de la respuesta:")
    print(respuesta)
    if ('asis_funciones' in respuesta and respuesta['asis_funciones']):
        asisFunciones = respuesta['asis_funciones']
        funciones = {
            'get_recomendaciones': controladorEdificios.getRecomendaciones,
            'get_ids_edificio_piso_ambiente': controladorEdificios.getInfoLugar,
        }

        resFunciones = []
        for afuncion in asisFunciones: 
            func = funciones[afuncion['funcion_name']]
            rcontent = func(afuncion['funcion_args'])

            if rcontent['info']:
                session['contenido'].append({"nombre": afuncion['funcion_name'], "valor": rcontent['info']})

            resFunciones.append({ "tool_call_id": afuncion['funcion_id'], "output": rcontent['reason'] })

        print(session.get('contenido'))
        print("Envio de funciones:")
        print(resFunciones)
        respuesta2 = controladorAsistente.enviarFunciones(resFunciones, respuesta['id_run'], session.get('idHilo'))
        return procesamientoConversacion(respuesta2['datos'])
    elif ('respuesta_msg' in respuesta  and respuesta['respuesta_msg']):
        return {
            'ok': True,
            'observacion': None,
            'datos': {"respuesta": respuesta['respuesta_msg'], "info": session.get('contenido')}
        }
    else:
        respuesta2 = controladorAsistente.getRespuesta(session.get('idHilo'), "No hubo respuesta por parte del asistente a la peticion previamente mencionada. Da una respuesta al usuario.")
        return {
            'ok': True,
            'observacion': None,
            'datos':  {"respuesta": respuesta2['respuesta_msg'], "info": session.get('contenido')}
        }

@app.get('/inicializarAnt')
def inicializarAsistenteAnt():
    global compMsgs
    compMsgs = []
    usuarioAct = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    session['user'] = usuarioAct
    tmpMensaje = getMensajeSistema()
    session['mensajes'] = tmpMensaje
    compMsgs = list(filter(lambda x: x['usuario'] != usuarioAct, compMsgs))
    return jsonify({'res': 1, 'user': usuarioAct})

@app.post('/conversar2')
def getRespuesta2():
    global compMsgs

    #genero = request.form['genero']
    mensaje = request.form['mensaje']
    mensajeList = json.loads(mensaje)

    mensTemp = session.get('mensajes')
    for melist in mensajeList:
        mensTemp.append(melist)
    
    mTmpAsis = list(mensTemp)
    #controlador = AsistenteControlador()
    respuesta = controladorAsistente.getRespuesta(session.get('user'), mTmpAsis, compMsgs)
    almacenar_msg = respuesta['almacenar_msg']
    if respuesta['mensaje']:
        nuevoCM = {"usuario": session.get('user'), "lastId": len(almacenar_msg), "data": respuesta['mensaje']}
        compMsgs.append(nuevoCM)
        almacenar_msg.append(str(respuesta['mensaje']))
    else:
        almacenar_msg.append({'role': 'assistant', 'content': respuesta['respuesta_msg']})
    
    session['mensajes'] = mensTemp
    return jsonify({"respuesta_msg": respuesta['respuesta_msg'], "asis_funciones": respuesta['asis_funciones']})

@app.post('/enviar-funciones')
def enviarFunciones():
    tcFunciones = request.form['toolcall_output']
    json_tcFunciones = json.loads(tcFunciones)
    idRun = request.form['id_run']

    if 'idHilo' not in session:
        return jsonify({
            'ok': False,
            'observacion': "No se tiene registros de conversacion. Por favor, recargue la pagina.",
            'datos': None
        })
    else:
        return controladorAsistente.enviarFunciones(json_tcFunciones, idRun, session.get('idHilo'))
    
@app.get('/lista-mensajes')
def listarMensajes():
    if 'idHilo' not in session:
        return jsonify({
            'ok': False,
            'observacion': "No se ha iniciado una conversacion con el asistente.",
            'datos': None
        })
    else:
        listaMensajes = controladorAsistente.getListaMensajes(session.get('idHilo'))
        return jsonify({
            'ok': True,
            'observacion': None,
            'datos': listaMensajes
        })

@app.get('/api/info_edificios_ambientes')
def getEdificiosAmbientes():
    controlador = AmbientesControlador()
    return jsonify(controlador.getAmbientesCompleta())



@app.post('/api/prediccion_datos')
def getPrediccion():
    #datos = request.get_json()
    
    """
    edificio = request.args.get('idEdificacion')
    piso = request.args.get('idPiso')
    ambiente = request.args.get('idAmbiente')
    fechaInicio = request.args.get('fechaInicio')
    fechaFin = request.args.get('fechaFin')
    """
    #datos = controladorEdificios.consumoSemana(edificio, piso, ambiente, fechaInicio, fechaFin)
    datos = request.get_json()

    respuesta = {
        'observacion': None,
        'ok': True,
        'datos': getPrediccionConsumo(datos)
    }
    return jsonify(respuesta)

@app.post('/api/ambientes')
def getAmbientes():
    edificio = request.form['edificio']
    controlador = AmbientesControlador()
    return jsonify(controlador.getAmbientes(edificio))

@app.post('/api/datos_consumo')
def getDatosConsumo():
    edificio = request.form['edificio']
    ambiente = request.form['ambiente']
    fecha = request.form['fecha']

    controlador = ConsumoControlador()
    consumoActual = controlador.getConsumoActual(edificio, ambiente, fecha)

    if consumoActual['res'] == 1:
        consumoFuturo = controlador.getConsumoFuturo(consumoActual['datos'])
        return jsonify({'data_actual': consumoActual, 'data_futuro': consumoFuturo})
    else:
        return jsonify({'data_actual': consumoActual})
    
@app.post('/api/validar_parametros')
def validarParametros():
    edificio = request.form['edificio']
    ambiente = request.form['ambiente']
    #fecha = request.form['fecha']

    controlEdificio = EdificiosControlador()
    controlAmbiente = AmbientesControlador()
    
    res = 0
    d_edificio = controlEdificio.validarEdificio(edificio)
    d_ambiente = None
    if d_edificio:
        res = 1
        d_ambiente = controlAmbiente.validarAmbiente(d_edificio['ID'], ambiente)
    
    return jsonify({'res': res, 'edificio': d_edificio['ID'], 'ambiente': d_ambiente['Codigo']})

if __name__ == '__main__':
    app.run(port=3005, debug=True, use_reloader=True, host='0.0.0.0', ssl_context=(os.environ.get("RUTA_CERT"), os.environ.get("RUTA_CERT_KEY")))
#    app.run(port=3002, debug=True, host='0.0.0.0')
