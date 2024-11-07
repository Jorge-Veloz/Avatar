/*
    Autor del código: Teddy Alejandro Moreira Vélez
    Descripción: Script de funcionamiento de interacciones del asistente e interfaz
    Fecha de creación: 14-10-2024
    Fecha de actualización: 03-11-2024
*/

if(window.webkitSpeechRecognition == undefined){
    Swal.fire({
        title:"Error",
        text:"Su navegador no soporta el reconocimiento de voz.\nIntente con otro navegador",
        icon:"error",
        showConfirmButton: false,
        allowOutsideClick: false,
        footer: '<a href="https://www.google.com/intl/es-419/chrome/">Se recomienda usar Chrome</a>'
    });
    $('#cod-form').attr('disabled', 'true');
    $('#fecha_atencion').attr('disabled', 'true');
}
if(window.SpeechSynthesisUtterance == undefined){
    Swal.fire({
        title:"Error",
        text:"Su navegador no soporta el interprete de texto a voz.\nIntente con otro navegador",
        icon:"error",
        showConfirmButton: false,
        allowOutsideClick: false,
        footer: '<a href="https://www.google.com/intl/es-419/chrome/">Se recomienda usar Chrome</a>'
    });
    $('#cod-form').attr('disabled', 'true');
    $('#fecha_atencion').attr('disabled', 'true');
}
if(window.SpeechSynthesis == undefined){
    Swal.fire({
        title:"Error",
        text:"Su navegador no soporta la reproduccion de voz.\nIntente con otro navegador",
        icon:"error",
        showConfirmButton: false,
        allowOutsideClick: false,
        footer: '<em>Se recomienda usar <a href="https://www.google.com/intl/es-419/chrome/">Chrome</a> o <a href="https://www.microsoft.com/es-es/edge/download">Edge</a></em>'
    });
    $('#cod-form').attr('disabled', 'true');
    $('#fecha_atencion').attr('disabled', 'true');
}

var estadoAsistente;
var asistenteFinalizo = false;
var conversacion = [];

var recognition;
var utterance;
var synth;
var voces;
var intervalo;
const TIEMPO_CORTE = 2;

var chConsumoAct;
var chConsumoFut;

//Inicializacion de los servicios
document.addEventListener("DOMContentLoaded", () => {
    /* ========================== Seteo Reconocimiento de Voz ========================== */
    recognition = new webkitSpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onaudiostart = (event) => {
        cambiaAnimacionAsistente('detener-asistente')
        estadoAsistente = "escuchando";
    }
    recognition.onaudioend = (event) => {
        cambiaAnimacionAsistente('hablar-asistente')
        estadoAsistente = "detenido";
    }
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
    
        conversacion.push({"role": "user", "content": transcript});
        conversarAsistente();
    };
    recognition.onerror = (event) => {
        cambiaAnimacionAsistente('hablar-asistente')
        Swal.fire("Error al reconocer la voz", "Error: "+event.error, "error");
        estadoAsistente = "esperando";
    };
    /* ========================== Fin Seteo Reconocimiento de Voz ========================== */

    /* ========================== Seteo Reproduccion de Voz ========================== */
    utterance = new SpeechSynthesisUtterance(); // Reproducira voz en base a texto
    synth = window.speechSynthesis;

    gestionarErrorVoz();

    utterance.lang = 'es-ES' || 'es-MX' || 'es-US' || 'en-US';
    /* ========================== Fin Seteo Reproduccion de Voz ========================== */

    /* ========================== Seteo Charts ========================== */
    //setearCharts();
    chConsumoAct = crearChart(document.querySelector("#grafica_cons_act"), 'line');
    chConsumoFut = crearChart(document.querySelector("#grafica_cons_fut"), 'line');
    /* ========================== Fin Seteo Charts ========================== */
    //$('#fecha_busqueda').val(new Date().toISOString().split('T')[0]);
    $('#asistente-btn').removeAttr('disabled');
    getEdificios();
    llenarModalInfoEdificios();
});

function llenarModalInfoEdificios(){
    fetch('/api/info_edificios_ambientes', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        if(data['res'] == 1){
            let datos = data['datos'];
            const groupedData = datos.reduce((acc, item) => {
                const { Nombre, Codigo } = item;
                if (!acc[Nombre]) {
                    acc[Nombre] = { Nombre, Codigos: [] };
                }
                acc[Nombre].Codigos.push(Codigo);
                return acc;
            }, {});
            
            const result = Object.values(groupedData);
            
            let htmlAcordion = "";
            for(let r of result){
                htmlAcordion += `<div class="accordion-item">
                            <h2 class="accordion-header">
                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse"
                                    data-bs-target="#flush-collapse${r['Nombre'].substr(0,3)}" aria-expanded="false" aria-controls="flush-collapse${r['Nombre'].substr(0,3)}">
                                    Edificio ${r['Nombre']}
                                </button>
                            </h2>
                            <div id="flush-collapse${r['Nombre'].substr(0,3)}" class="accordion-collapse collapse" data-bs-parent="#accordionFlushExample">
                                <div class="accordion-body">
                                    <ul>`;
                for(let a of r['Codigos']){
                    htmlAcordion += `<li>Ambiente ${a}</li>`;
                }
                                        
                                    htmlAcordion += `</ul>
                                </div>
                            </div>
                        </div>`;
            }
            $('#accordionFlushExample').html(htmlAcordion);
        }
    })
}

function getEdificios(){
    fetch('/api/edificios', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        if(data['res'] == 1){
            let datos = data['datos'];

            let ops = "<option value='' selected disabled>Seleccione el edificio</option>";
            for(let d of datos){
                ops += `<option value='${d['ID']}'>${d['Nombre']}</option>`;
            }
            $('#combo_edificio').html(ops);
        }
    })
}

function getAmbiente(){
    let formData = new FormData();
    formData.append('edificio', $('#combo_edificio').val());

    fetch('/api/ambientes', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if(data['res'] == 1){
            let datos = data['datos'];

            let ops = "<option value='' selected disabled>Seleccione el ambiente</option>";
            for(let d of datos){
                ops += `<option value='${d['Codigo']}'>${d['Descripcion']}</option>`;
            }
            $('#combo_ambientes').html(ops);
        }
    })
}

function consultarDatosEnergeticos(){
    let edificio = $('#combo_edificio').val();
    let ambiente = $('#combo_ambientes').val();
    let fecha = $('#fecha_busqueda').val();

    if(!(edificio || ambiente || fecha)){
        Swal.fire('', 'Se requieren los campos Edificio, Ambientes y Fecha', 'error');
        return;
    }

    informacionConsumo(edificio, ambiente, fecha);
}

function informacionConsumo(edificio, ambiente, fecha){
    let formData = new FormData();
    formData.append('edificio', edificio);
    formData.append('ambiente', ambiente);
    formData.append('fecha', fecha);
    fetch('/api/datos_consumo', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        let data_actual = data['data_actual'];
        if(data_actual['res'] == 1){
            let datos = data_actual['datos'];
            
            let consumo_actual = [];
            for(let ca of datos['consumo_actual']){
                consumo_actual.push({x: ca['Mes'], y: ca['Consumo_Mensual']})
            }
            
            let consumo_actual_total = [];
            for(let cat of datos['consumo_actual_total']){
                consumo_actual_total.push({x: cat['Mes'], y: cat['Consumo_Mensual']})
            }
            
            let dataConsumo = [{
                name: "Consumo Actual",
                data: consumo_actual
            }, {
                name: "Consumo Total",
                data: consumo_actual_total
            }];
            console.log(dataConsumo)
            
            chConsumoAct.updateSeries(dataConsumo);

            $('#val_consact_amb').text(datos['consumo_actual'][datos['consumo_actual'].length-1]['Consumo_Mensual'] + "kWh");
            $('#val_consact_edi').text(datos['consumo_actual_total'][datos['consumo_actual_total'].length-1]['Consumo_Mensual'] + "kWh");

            let data_futuro = data['data_futuro'];
            if(data_futuro && data_futuro['res'] == 1){
                let datos = data_futuro['datos'];
                console.log(datos);
            
                let consumo_futuro = [];
                for(let cf of datos['consumo_futuro']){
                    consumo_futuro.push({x: cf['Mes'], y: cf['Consumo_Mensual'].toFixed(2)})
                }
                
                let consumo_futuro_total = [];
                for(let cft of datos['consumo_futuro_total']){
                    consumo_futuro_total.push({x: cft['Mes'], y: cft['Consumo_Mensual'].toFixed(2)})
                }
                
                let dataConsumo = [{
                    name: "Consumo Futuro",
                    data: consumo_futuro
                }, {
                    name: "Consumo Total",
                    data: consumo_futuro_total
                }];
                console.log(dataConsumo)
                
                chConsumoFut.updateSeries(dataConsumo);

                $('#val_consfut_amb').text(datos['consumo_futuro'][datos['consumo_futuro'].length-1]['Consumo_Mensual'].toFixed(2) + "kWh");
                $('#val_consfut_edi').text(datos['consumo_futuro_total'][datos['consumo_futuro_total'].length-1]['Consumo_Mensual'].toFixed(2) + "kWh");
            }
        }else{
            Swal.fire("", "No se encontro informacion en base a los parametros consultados.", "error");
        }
    })
}

function inicializarAsistente(){
    cambiaAnimacionAsistente("cargando-asistente");
    fetch('/inicializar', {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        asistenteFinalizo = false;
        
        if(data['res'] == 1){
            let txtInicio = "Presentate ante el usuario y dale una bienvenida. Tienes que preguntarle al usuario sobre su nombre y si es estudiante o docente.";
            conversacion.push({'role': 'user', 'content': txtInicio});
            conversarAsistente();
        }
        //cambiaAnimacionAsistente("hablar-asistente");
    })
}

/*function getConsumoActual(edificio, ambiente, fecha){
    const formData = new FormData();
    formData.append('edificio', edificio);
    formData.append('ambiente', ambiente);
    formData.append('fecha', fecha);
    fetch('/api/consumoActual', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        
    })
}*/

function cambiaAnimacionAsistente(animacion){
    let clasesAnim = [
        "inicializar-asistente",
        "cargando-asistente",
        "hablar-asistente",
        "detener-asistente",
        "reproduciendo-asistente"
    ];

    for(let ca of clasesAnim){
        if($('#inner-wave').hasClass(ca)){
            $('#inner-wave').removeClass(ca);
        }
    }

    $('#inner-wave').removeAttr('disabled');

    switch(animacion){
        case 'inicializar-asistente':
        {
            $('#inner-wave').addClass(animacion);
            $('#icon_control').html('<i class="fa-solid fa-play"></i>');
            $('#icon_control').attr('title', 'Iniciar Asistente');
        }
        break;
        case 'cargando-asistente':
        {
            $('#inner-wave').addClass(animacion);
            $('#icon_control').html('<i class="fa-solid fa-circle-notch"></i>');
            $('#icon_control').attr('title', 'Procesando...');
            $('#inner-wave').attr('disabled', true);
        }
        break;
        case 'hablar-asistente':
        {
            $('#inner-wave').addClass(animacion);
            $('#icon_control').html('<i class="fa-solid fa-microphone"></i>');
            $('#icon_control').attr('title', 'Hablar');
        }
        break;
        case 'detener-asistente':
        {
            $('#inner-wave').addClass(animacion);
            $('#icon_control').html('<i class="fa-solid fa-microphone"></i>');
            $('#icon_control').attr('title', 'Dejar de hablar');
        }
        break;
        case 'reproduciendo-asistente':
        {
            $('#inner-wave').addClass(animacion);
            $('#icon_control').html('<i class="fa-solid fa-volume-high"></i>');
            $('#icon_control').attr('title', 'Asistente hablando...');
            $('#inner-wave').attr('disabled', true);
        }
        break;
    }

    /*if(animacion != "estatica"){
        $('#outer-circle').removeClass('oc-pulsing');
        $('#inner-wave').addClass(animacion);
    }else{
        $('#outer-circle').addClass('oc-pulsing');
    }*/
}

function gestionarErrorVoz(){
    if (synth.speaking || synth.pending) {
        console.log("El sistema sigue hablando, se procede a cancelarlo.");
        synth.cancel();
    }
}

async function hablar(texto) {
    gestionarErrorVoz();

    const speechChunks = makeCunksOfText(texto);
    let indice = 0;

    /*if(!$('#inner-wave').hasClass('iw-enabled')){
        $('#inner-wave').addClass('iw-enabled');
    }*/

    utterance.onstart = function(){
        clearTimeout(intervalo);
        if(indice == 1){
            cambiaAnimacionAsistente("reproduciendo-asistente");
            estadoAsistente = "detenido"
        }
    }

    // Manejar el evento 'end' para liberar el speaking
    utterance.onend = function() {
        //clearTimeout(intervalo);
        if(indice < speechChunks.length){
            console.log("La reproducción del texto ha terminado.");
            indice = voz(speechChunks[indice], indice);
            /*if (speechChunks.length - 1 == indice) {
                
            }*/
        }else{
            gestionarErrorVoz();
            console.log("El texto ha terminado de reproducirse.");
            cambiaAnimacionAsistente("hablar-asistente");
            estadoAsistente = "esperando";
            
            if(asistenteFinalizo){
                $('#inner-wave').removeClass('iw-enabled');
                guardarFormulario();
                estadoAsistente = "detenido";
            }
        }
    };

    // Capturar errores de síntesis de voz
    utterance.onerror = function(event) {
        console.error('Error durante la síntesis de voz:', event.error);
        clearTimeout(intervalo);

        let err_ind = (indice <= 0) ? 0 : indice -1;
        indice = voz(speechChunks[err_ind], err_ind);
    };

    // Eventos adicionales para medir el estado de la sintesis de voz
    utterance.onpause = (vBoundary) => {
        console.log("Boundary event: " + vBoundary);
    };

    utterance.onboundary = (vPause) => {
        console.log("Pause event: " + vPause);
    };
    
    utterance.onresume = (vResume) => {
        console.log("Resume event: " + vResume);
    };
    utterance.onmark = (vMark) => {
        console.log("Mark event: " + vMark);
    };

    indice = voz(speechChunks[indice], indice);
}

function voz(texto, indice){
    intervalo = setTimeout(() => {
        synth.cancel();
    }, TIEMPO_CORTE * 1000);

    utterance.text = texto;
    synth.speak(utterance);

    return indice + 1;
}

function makeCunksOfText(text) {
    const maxLength = 220; // entre 190 y 220
    let speechChunks = [];

    // Split the text into chunks of maximum length maxLength without breaking words
    while (text.length > 0) {
        if (text.length <= maxLength) {
            speechChunks.push(text);
            break;
        }

        let chunk = text.substring(0, maxLength + 1);

        let lastPointIndex = chunk.lastIndexOf('.');
        let lastSpaceIndex = chunk.lastIndexOf(' ');
        if (lastPointIndex !== -1) {
            speechChunks.push(text.substring(0, lastPointIndex));
            text = text.substring(lastPointIndex + 1);

        } else if (lastSpaceIndex !== -1) {
            speechChunks.push(text.substring(0, lastSpaceIndex));
            text = text.substring(lastSpaceIndex + 1);

        } else {
            // If there are no spaces in the chunk, split at the maxLength
            speechChunks.push(text.substring(0, maxLength));
            text = text.substring(maxLength);
        }
    }

    return speechChunks
}

/* EVENTOS DE ESCUCHA DEL NAVEGADOR */

function toggleEscucha(){
    if(estadoAsistente){
        if(estadoAsistente == "esperando"){
            iniciarEscucha();
        }else if(estadoAsistente == "escuchando"){
            detenerEscucha();
        }
    }else{
        estadoAsistente = "detenido";
        inicializarAsistente();
    }
}

function iniciarEscucha(){
    recognition.start();
}

function detenerEscucha(){
    recognition.stop();
}

// hace posible la conversacion con el asistente
function conversarAsistente(){
    const formData = new FormData();
    formData.append('mensaje', JSON.stringify(conversacion));
    console.log(conversacion);
    fetch('/conversar', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(respuesta => {
        if(!$('#contenedor-typing').hasClass('ct-appear')){
            $('#contenedor-typing').addClass('ct-appear');
        }
        conversacion = [];
        if(respuesta['asis_funciones']){
            ejecutarFuncion(respuesta['asis_funciones']);
            //console.log(respuesta);

        }else if(respuesta['respuesta_msg']){
            let textType = document.getElementById('typeContenido');
            let rMensaje = respuesta['respuesta_msg']
            let iTextChar = 0;

            textType.textContent = "";
            idInt = setInterval(() => {
                if (iTextChar < rMensaje.length) {
                    textType.textContent += rMensaje.charAt(iTextChar);
                    iTextChar++;
                }else{
                    clearInterval(idInt);
                }
            }, 55);
            hablar(rMensaje);
            conversacion.push({"role": "assistant", "content": rMensaje});
        }
    });
}

async function ejecutarFuncion(asisFunciones){
    console.log(asisFunciones);
    let handleAFunciones = {
        'get_usuario': getDatosUsuario,
        'get_ambiente_edificio': getAmbienteEdificio,
        'get_edificios': mostrarInfoEdificios,
        /*'sfromgenero': getSintomasxGenero,
        'get_diagnostico': getDiagnostico,
        'get_tratamiento': getTratamiento,
        'finalizar': finalizarAsistente,
        'guardar_form': guardarxAsistente*/
    }

    for(let afuncion of asisFunciones){
        //afuncion['funcion']
        //afuncion['funcion_args'] = JSON.parse(afuncion['funcion_args']);
        //console.log(afuncion);
        const activarFuncion = handleAFunciones[afuncion['funcion_name']];

        let rcontent = await activarFuncion(afuncion);
        let respuestaF = {
            "tool_call_id": afuncion['funcion_id'],
            "role": "tool",
            "name": afuncion['funcion_name'],
            "content": rcontent,
        };
        conversacion.push(respuestaF);
    }
    conversarAsistente();
}

async function getDatosUsuario(respuesta){
    let fArgumentos = respuesta['funcion_args'];

    if(fArgumentos['cargo'] && fArgumentos['nombres']){
        return JSON.stringify({success: true}); 
    }else if(fArgumentos['cargo']){
        return "Pidele al usuario que te indique su nombre"
    }else if(fArgumentos['nombres']){
        return "Preguntale al usuario si es estudiante o docente"
    }else{
        return "Vuelve a preguntarle al usuario su nombre y si es estudiante o docente"
    }
}

async function getAmbienteEdificio(respuesta){
    /*let fArgumentos = respuesta['funcion_args'];

    if(fArgumentos['edificio'] && fArgumentos['ambiente']){
        console.log(fArgumentos);
        //fetch('/api/')
        let formData = new FormData();
        formData.append('edificio', fArgumentos['edificio']);
        formData.append('ambiente', fArgumentos['ambiente']);

        fetch('/api/validar_parametros', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            console.log(data)
            if(data['res'] == 1){
            }
            return "Informale al usuario que se mostrara la informacion del consumo energetico en pantalla a continuacion."; 
        })
    }else{
        return "Vuelve a preguntarle al usuario sobre el edificio y el ambiente que desea consultar."
    }*/

    let fArgumentos = respuesta['funcion_args'];

    if (fArgumentos['edificio'] && fArgumentos['ambiente']) {
        console.log(fArgumentos);
        let formData = new FormData();
        formData.append('edificio', fArgumentos['edificio']);
        formData.append('ambiente', fArgumentos['ambiente']);

        try {
            // Espera a que fetch se resuelva
            let response = await fetch('/api/validar_parametros', {
                method: 'POST',
                body: formData
            });
            let data = await response.json();
            console.log(data);

            // Verifica el resultado de la respuesta
            if (data['res'] == 1) {
                if(data['ambiente']){
                    informacionConsumo(data['edificio'], data['ambiente'], '2024-01-10');
                    return "Informale al usuario que se mostrará la información del consumo energético en pantalla a continuación. Además dale unas recomendaciones para optimizar el consumo energetico del edificio y ambientes."; 
                }else{
                    return "Informale al usuario que ese ambiente no se encuentra registrado como parte del edificio."; 
                }
            } else {
                return "Informale al usuario que no se encontro el edificio solicitado. Recuerdale al usuario que te puede pedir mostrar los edificios registrados.";
            }
        } catch (error) {
            console.error("Error en la solicitud:", error);
            return "Ocurrió un error al consultar los datos. Inténtalo de nuevo.";
        }
    }else{
        return "Vuelve a preguntarle al usuario sobre el edificio y el ambiente que desea consultar."
    }
}

async function mostrarInfoEdificios(respuesta){
    let fArgumentos = respuesta['funcion_args'];

    $('#modalInfoEdificios').modal('show');
    /*if(fArgumentos['mostrar']){
    }*/
    return "Informale al usuario que se esta mostrando la informacion de los edificios y sus ambientes";
}

function setearCharts(){
    let dataConsAct = [
        {
            name: 'Consumo Actual',
            data: [30,40,35,50,49,60,70,91,125]
        },{
            name: 'Consumo Total',
            data: [40,45,60,22,32,14,18,78,150]
        }
    ];
    var chConsumoAct = crearChart(document.querySelector("#grafica_cons_act"), 'line', dataConsAct);
    
    let dataConsFut = [
        {
            name: 'Consumo Futuro',
            data: [30,40,35,50,49,60,70,91,125]
        },{
            name: 'Consumo Total',
            data: [40,45,60,22,32,14,18,78,150]
        }
    ];
    var chConsumoFut = crearChart(document.querySelector("#grafica_cons_fut"), 'line', dataConsFut);
}

function crearChart(elemento, tipo){
    let options = {
        chart: {
            type: tipo,
            height: '100%',
            width: '100%'
        },
        series: [{
            name: "Series default",
            data: [0, 0, 0]
        }],
        xaxis: {
            type: "datetime"
        }
    };
    
    let chart = new ApexCharts(elemento, options);
    
    chart.render();

    return chart;
}