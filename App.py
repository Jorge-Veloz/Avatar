from flask import Flask, render_template, url_for, request, session, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from controladores.asistente import AsistenteControlador
from controladores.edificios import EdificiosControlador
from controladores.ambientes import AmbientesControlador
from controladores.chats import ChatsControlador
from controladores.consumo import ConsumoControlador
#from controladores.tts import TTSControlador
#from controladores.modelosia import IAControlador
#from controladores.speech import SpeechController
from funciones.asistente import getMensajeSistema
from funciones.algoritmos import getPrediccionConsumo, detectar_intencion
#from config import Config
#from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy.sql import text
import json
import os
from dotenv import load_dotenv
import requests
import random
import string

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
        data={'id': id}
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
        data={'texto': resultado['datos']['respuesta'], 'id': id}
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
    if 'memoria' in session: session.pop('memoria')
    
    hilo = controladorAsistente.crearHilo()
    
    session['hilo'] = hilo
    mensajeInicial = {"role":"user", "content": "El usuario se ha conectado, preséntate ante el usuario y dale una bienvenida."}
    respuesta = controladorAsistente.getRespuesta(session.get('hilo'), [mensajeInicial]) #enviar el identificador para obtener historial
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
        data={'texto': resultado['datos']['respuesta'], 'id': session.get('hilo')}
    )

    #encoded = response1['datos']['voice_encoded']
    encoded = response1.json()['datos']['voice_encoded']
    resultado['datos']['audio'] = encoded
    
    return jsonify(resultado)

@app.post('/conversar')
def getRespuesta():
    #mensaje = request.form['mensaje']
    
    #print(session['hilo'])
    if 'hilo' not in session:
        hilo = controladorAsistente.crearHilo()
        session['hilo'] = hilo

    codigo = session.get('hilo')
    ruta = f'{rutaGrabacion}/input-{codigo}.mp3'
    request.files['voice'].save(ruta)
    #voz = request.files['voice']
    response = requests.post(
        url=os.environ.get("RUTA_VOZ")+'/voz_texto',
        files={'voice': ('voice.mp3', open(ruta, 'rb'))},
        data={'id': session.get('hilo')} 
    )
    #response = controladorTTS.SpeechToText(voz, codigo)

    
    #text = response['datos']
    text = response.json()['datos']
    if not text.strip():
        text = 'No pude entender lo que dijiste, Podrías repetirlo porfavor?'
    print(text)

    mensajeAsistente = {"role":"user", "content": text}
    datos = procesamientoConversacion(text)

    mensajesAsis = []
    mensajesAsis.append(mensajeAsistente)
    if datos: mensajesAsis.append(datos)
    
    respuesta = controladorAsistente.getRespuesta(session.get('hilo'), mensajesAsis)
    #session['contenido'] = []
    #resultado = procesamientoConversacion(respuesta['datos'])
    
    # With API
    # response1 = requests.post(
    #     url=os.environ.get("RUTA_VOZ")+'/texto_voz',
    #     data={'texto': resultado['datos']['respuesta'], 'id': session.get('hilo')}
    # )

    resultado = {
        'ok': True,
        'observacion': None,
        'datos': {"respuesta": respuesta['datos'], "info": session.get('contenido')}
    }

    #response1 = controladorTTS.TextToSpeech(respuesta['datos'], codigo)
    response1 = requests.post(
        url=os.environ.get("RUTA_VOZ")+'/texto_voz',
        data={'texto': resultado['datos']['respuesta'], 'id': session.get('hilo')}
    )

    #encoded = response1['datos']['voice_encoded']
    encoded = response1.json()['datos']['voice_encoded']
    resultado['datos']['audio'] = encoded

    return jsonify(resultado)

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

def procesamientoConversacion(texto):
    session['contenido'] = []
    funciones = {
        'solicita_recomendaciones': controladorEdificios.getRecomendaciones,
        'solicita_datos_consumo': controladorEdificios.consultarConsumo
    }
    etiquetas = list(funciones.keys())
    etiquetas.append('pregunta_respuesta_general')
    resultado = detectar_intencion(texto, etiquetas)
    intencion =  'pregunta_respuesta_general' if resultado['intencion'] not in etiquetas else resultado['intencion']

    if intencion != 'pregunta_respuesta_general':
        funcionIA = funciones[intencion]
        respuesta = funcionIA(texto)
        if respuesta['info']:
            session['contenido'].append({"nombre": intencion, "valor": respuesta['info']})
        return {"role": "user", "content": respuesta['reason']}
    else:
        return None
        

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
    datos = request.get_json()
    #controlador = ConsumoControlador()
    #return jsonify(controlador.getConsumoFuturo(datos))
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
    app.run(port=3005, debug=True, host='0.0.0.0', ssl_context=(os.environ.get("RUTA_CERT"), os.environ.get("RUTA_CERT_KEY")))
    #app.run(port=3005, debug=True, host='0.0.0.0')