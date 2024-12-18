from flask import Flask, render_template, url_for, request, session, jsonify, send_from_directory
from flask_jwt_extended import JWTManager
from controladores.asistente import AsistenteControlador
from controladores.edificios import EdificiosControlador
from controladores.ambientes import AmbientesControlador
from controladores.consumo import ConsumoControlador
from funciones.asistente import getMensajeSistema
import json
import os
from dotenv import load_dotenv
import random
import string

load_dotenv(os.path.join(os.getcwd(), '.env'))

# Guardara todos los ChatCompletions de respuesta a las funciones del asistente
# Esto evita que el asistente vuelva a repetir el envio de la funcion
compMsgs = []

app = Flask(__name__)
app.config['SECRET_KEY'] = b'secret_key'

# Inicializacion del JWT
jwt = JWTManager(app)
 
with app.test_request_context():
    url_for('static', filename='/resources/')
    url_for('static', filename='/css/')
    url_for('static', filename='/scripts/')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('static', filename)

@app.get('/')
def Index():
    return render_template('3d.html')

@app.get('/avatar')
def modeloAvatar():
    return render_template('avatar.html')

@app.get('/inicializar')
def getPaciente():
    global compMsgs
    compMsgs = []
    usuarioAct = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    session['user'] = usuarioAct
    tmpMensaje = getMensajeSistema()
    session['mensajes'] = tmpMensaje
    compMsgs = list(filter(lambda x: x['usuario'] != usuarioAct, compMsgs))
    return jsonify({'res': 1, 'user': usuarioAct})

@app.post('/conversar')
def getRespuesta():
    global compMsgs

    #genero = request.form['genero']
    mensaje = request.form['mensaje']
    mensajeList = json.loads(mensaje)

    mensTemp = session.get('mensajes')
    for melist in mensajeList:
        mensTemp.append(melist)
    
    mTmpAsis = list(mensTemp)
    controlador = AsistenteControlador()
    respuesta = controlador.getRespuesta(session.get('user'), mTmpAsis, compMsgs)
    almacenar_msg = respuesta['almacenar_msg']
    if respuesta['mensaje']:
        nuevoCM = {"usuario": session.get('user'), "lastId": len(almacenar_msg), "data": respuesta['mensaje']}
        compMsgs.append(nuevoCM)
        almacenar_msg.append(str(respuesta['mensaje']))
    else:
        almacenar_msg.append({'role': 'assistant', 'content': respuesta['respuesta_msg']})
    
    session['mensajes'] = mensTemp
    return jsonify({"respuesta_msg": respuesta['respuesta_msg'], "asis_funciones": respuesta['asis_funciones']})

@app.get('/api/info_edificios_ambientes')
def getEdificiosAmbientes():
    controlador = AmbientesControlador()
    return jsonify(controlador.getAmbientesCompleta())

@app.get('/api/edificios')
def getEdificios():
    controlador = EdificiosControlador()
    return jsonify(controlador.getEdificios())

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
    app.run(port=3000, debug=True)