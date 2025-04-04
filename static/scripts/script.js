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
}else{
    comprobarPermisos('microfono');
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

/*if(!(localStorage.getItem('voz_asistente'))){
    if(!(/Android|iPhone|iPad/i.test(navigator.userAgent))) $('#modal_voces').modal('show');
}*/

//var vAsistente;
var estadoAsistente;
var asistenteFinalizo = false;
var conversacion = [];

let resolverPromAutor;
let rechazarPromAutor;

var recognition;
var utterance;
var synth;
var voces;
var intervalo;
const TIEMPO_CORTE = 2;
const rutaAPI = "http://192.168.0.247:3000/v1/asistente-virtual";

var chConsumoAct;
var chConsumoFut;
var dataConsumoAct;
var dataConsumoFut;
var permiteGraficaClic = false;

//Inicializacion de los servicios
document.addEventListener("DOMContentLoaded", () => {
    probarAPI();
    if(localStorage.getItem('autorizacion') == 1){
        inicializarDOM();
    }else{
        $('#modal_autorizacion').modal('show');
        verificarAutorizacion()
        .then((res)=>{
            $('#modal_autorizacion').modal('hide');
            localStorage.setItem('autorizacion', 1);
            inicializarDOM();
        })
        .catch((err) =>{
            localStorage.setItem('autorizacion', 0);
            location.href = "https://www.google.com/";
        });
    }
});

function probarAPI(){
    fetch('/pruebaAPI', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
    })
}

function inicializarDOM(){
    cambiaAnimacionAsistente('deshabilitado-asistente');
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
        cambiaAnimacionAsistente('cargando-asistente')
        estadoAsistente = "detenido";
    }
    recognition.onresult = (event) => {
        //cambiaAnimacionAsistente('cargando-asistente');
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

    if(/Android|iPhone|iPad/i.test(navigator.userAgent)){
        cambiaAnimacionAsistente('inicializar-asistente');
        utterance.lang = 'es-ES' || 'es-MX' || 'es-US' || 'en-US';
    }else if(/Macintosh/i.test(navigator.userAgent)){
        //toggleLoading('mostrar', 'Buscando voces...');

        synth.addEventListener("voiceschanged", setearVoces());
    }else{
        //toggleLoading('mostrar', 'Buscando voces...');

        synth.onvoiceschanged = setearVoces;
    }

    //utterance.lang = 'es-ES' || 'es-MX' || 'es-US' || 'en-US';
    /* ========================== Fin Seteo Reproduccion de Voz ========================== */

    /* ========================== Seteo Charts ========================== */
    //setearCharts();
    chConsumoAct = crearChart(document.querySelector("#grafica_cons_act"), 'line', 'grafica_actual');
    chConsumoFut = crearChart(document.querySelector("#grafica_cons_fut"), 'line', 'grafica_futuro');
    /* ========================== Fin Seteo Charts ========================== */
    //$('#fecha_busqueda').val(new Date().toISOString().split('T')[0]);
    $('#asistente-btn').removeAttr('disabled');
    getEdificios();
    //llenarModalInfoEdificios();
}

function verificarAutorizacion(){
    return new Promise((resolve, reject) => {
        resolverPromAutor = resolve;
        rechazarPromAutor = reject;
    })
}

function clickAutorizacion(accion){
    if(accion == 'A' && resolverPromAutor){
        resolverPromAutor('Autorizacion aceptada');
        resolverPromAutor = null;
        rechazarPromAutor = null;
    }else if(accion == 'R' && rechazarPromAutor){
        rechazarPromAutor('Autorizacion rechazada');
        resolverPromAutor = null;
        rechazarPromAutor = null;
    }else{
        Swal.fire('Ocurrio un error al procesar la accion.')
        .then(r => {
            location.href='https://www.google.com/';
        });
    }
}

function setearVoces(){
    //toggleLoading('ocultar');

    voces = window.speechSynthesis.getVoices();
    if(!localStorage.getItem('voz_asistente')){
        let vAsistente = voces.find(voz => voz.name === "Google español");

        if(vAsistente){
            cambiaAnimacionAsistente('inicializar-asistente');
            localStorage.setItem('voz_asistente', vAsistente.voiceURI);
            utterance.voice = voces.find(voz => voz.voiceURI === localStorage.getItem('voz_asistente'));
        }else{
            selectorVoces();
        }
    }else{
        cambiaAnimacionAsistente('inicializar-asistente');
        //vAsistente = voces.find(voz => voz.voiceURI === localStorage.getItem('voz_masculino'));
        utterance.voice = voces.find(voz => voz.voiceURI === localStorage.getItem('voz_asistente'));
    }
    //utterance.lang = 'es-ES' || 'es-MX' || 'es-US' || 'en-US';
    //console.log(localStorage.getItem(`voz_${generoAsistente}`));
}

function verificarVoz(){
    let vAsis = $('#select_voz').val();
    //console.log(vMasc + vFem);
    if(vAsis){
        $('#guardar_voz').attr('disabled', false);
    }else{
        $('#guardar_voz').attr('disabled', true);
    }
}

function selectorVoces(){
    let vES = voces.filter(v => v.lang == 'es-MX' || v.lang == 'es-ES' || v.lang == 'es-US');
    let opcHTML = "<option value='' selected disabled>Seleccione voz...</option>";

    for(let v of vES){
        opcHTML += `<option value="${v.voiceURI}">${v.name}</option>`;
    }

    console.log(opcHTML);

    $('#select_voz').html(opcHTML);
    $('#modal_voces').modal('show');
}

function reproducir(){
    gestionarErrorVoz();

    let selectVoz;
    
    let texto = "Hola, soy el asistente de consumo energetico";

    let vozURI = $('#select_voz').val();
    if(!vozURI){
        return;
    }
    selectVoz = voces.find(voz => voz.voiceURI === $('#select_voz').val());

    utterance.text = texto;
    utterance.voice = selectVoz;
    synth.speak(utterance);
    $('#play_voz').attr('disabled', true);

    utterance.onend = () => {
        $('#play_voz').removeAttr('disabled');
    }
}

function guardarVocesDefault(){
    //toggleLoading('mostrar', 'Guardando voces...')
    let vAsistente = $('#select_voz').val();

    localStorage.setItem('voz_asistente', vAsistente);
    utterance.voice = voces.find(voz => voz.voiceURI === localStorage.getItem('voz_asistente'));

    //toggleLoading('ocultar')
    $('#modal_voces').modal('hide');

    Swal.fire('Se ha guadado la voz correctamente.', '', 'success').then(r => {
        cambiaAnimacionAsistente('inicializar-asistente');
    });
}

function llenarModalInfoEdificiosAnt(){
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

function llenarModalInfoEdificios(data){
    let htmlAcordion = ``;
    let datos = data['datos'];

    if(datos.length > 0){
        datos.forEach((d, indexEdi) => {
            //let listaEdificios = ``
            htmlAcordion += `<div class="accordion-item">
                                <h2 class="accordion-header" id="flush-headingEdificios${indexEdi}">
                              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseEdificios${indexEdi}" aria-expanded="false" aria-controls="flush-collapseEdificios${indexEdi}">
                                    ${d['nombre']}
                              </button>
                            </h2>
                            <div id="flush-collapseEdificios${indexEdi}" class="accordion-collapse collapse" aria-labelledby="headingEdificios${indexEdi}" data-bs-parent="#accordionFlushExample">
                                <div class="accordion-body p-0 ps-3">`;
            if(d['pisos'].length > 0){
                htmlAcordion += `<div class="accordion accordion-flush" id="accordionFlushExampleEdificio${indexEdi}">`;
                d['pisos'].forEach((p, indexPiso)=>{
                    htmlAcordion += `<div class="accordion-item">
                                    <h2 class="accordion-header" id="flush-headingPiso${indexPiso}">
                                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapsePiso${indexPiso}" aria-expanded="false" aria-controls="flush-collapsePiso${indexPiso}">
                                            ${p['nombre']}
                                        </button>
                                    </h2>
                                    <div id="flush-collapsePiso${indexPiso}" class="accordion-collapse collapse" aria-labelledby="flush-headingPiso${indexPiso}" data-bs-parent="#accordionFlushExampleEdificio${indexEdi}">
                                        <div class="accordion-body p-0 ps-3">`;
                    if(p['ambientes'].length > 0){
                        htmlAcordion += `<ul class="list-group list-group-flush">`;
                        p['ambientes'].forEach((a, indexAmbiente) => {
                            htmlAcordion += `<li class="list-group-item">${a['nombre']}</li>`;
                        });
                        htmlAcordion += `</ul>`;
                    }
                    htmlAcordion += `</div></div></div>`;
                })
                htmlAcordion += `</div>`;
            }else{
                //listaEdificios += `<li class="list-group-item">${d['nombre']}</li>`;
            }
            htmlAcordion += `</div></div></div>`;
            //htmlAcordion += `<ul class="list-group list-group-flush">${listaEdificios}</ul>`
        });
        
    }
    
    $('#accordionFlushExample').html(htmlAcordion);
    
}

function getEdificiosAntiguo(){ //Funcion de la API antigua
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

function getEdificios(){ //Funcion de la nueva API
    fetch(rutaAPI+'/edificios', {
        method: 'GET'
    })
    .then(response => {
        return response.json();
        if(response.ok){
            return response.json();
        }else{
            //return response.text();
            if(response.status >= 400 && response.status < 500){
                throw new Error("El servicio no esta disponible. Por favor, intente despues.");
            }else{
                throw new Error("Ocurrio un problema con el servidor.");
            }
        }
    })
    .then(data => {
        
        if(data.ok){
            console.log(data);
            let datos = data['datos'];

            let ops = "<option value='' selected disabled>Seleccione el edificio</option>";
            for(let d of datos){
                ops += `<option value='${d['id']}'>${d['nombre']}</option>`;
            }
            $('#combo_edificio').html(ops);
            llenarModalInfoEdificios(data);
        }else{
            $('#combo_edificio').html("<option value='' selected disabled>No hay datos de edificios</option>");
            Swal.fire('Error', data.observacion, 'error');
        }
        /*if(data.length > 0){
        }else{
        }*/
    })
    .catch(error => {
        Swal.fire("Error en el servidor.", "Error: "+error.message, "error");
    });
}

function getPiso(){
    let edificio = $('#combo_edificio').val();
    fetch(rutaAPI+'/pisos?idEdificacion='+edificio, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        /*if(data['res'] == 1){
            let datos = data['datos'];

            let ops = "<option value='' selected disabled>Seleccione el ambiente</option>";
            for(let d of datos){
                ops += `<option value='${d['Codigo']}'>${d['Descripcion']}</option>`;
            }
            $('#combo_ambientes').html(ops);
        }*/

        if(data.ok){
            console.log(data);
            let datos = data['datos'];
    
            let ops = "<option value='' selected disabled>Seleccione el piso</option>";
            for(let d of datos){
                ops += `<option value='${d['id']}'>${d['nombre']}</option>`;
            }
            $('#combo_pisos').html(ops);
        }else{
            $('#combo_pisos').html("<option value='' selected disabled>No hay datos de pisos</option>");
            Swal.fire('Error', data.observacion, 'error');
        }
    })
}

function getAmbienteAnt(){
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

function groupBy(arr, prop) {
    const map = new Map(Array.from(arr, obj => [obj[prop],
    []
    ]));
    arr.forEach(obj => map.get(obj[prop]).push(obj));
    return Array.from(map.values());
}

function getAmbiente(){
    
    let edificio = $('#combo_edificio').val();
    let piso = $('#combo_pisos').val();
    fetch(rutaAPI+'/ambientes?idEdificacion='+edificio+'&idPiso='+piso, {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        /*if(data['res'] == 1){
            let datos = data['datos'];

            let ops = "<option value='' selected disabled>Seleccione el ambiente</option>";
            for(let d of datos){
                ops += `<option value='${d['Codigo']}'>${d['Descripcion']}</option>`;
            }
            $('#combo_ambientes').html(ops);
        }*/

        if(data.ok){
            console.log(data);
            let datos = data['datos'];
    
            /*let ops = "<option value='' selected disabled>Seleccione el ambiente</option>";
            for(let d of datos){
                ops += `<option value='${d['id']}'>${d['nombre']}</option>`;
            }
            $('#combo_ambientes').html(ops);*/

            let result = ``;
            let tipos = groupBy(datos, 'tipoAmbiente')
            tipos.forEach(i => {
                result += `<optgroup label="${i[0].tipoAmbiente}">`;
                i.forEach(j => { result += ` <option value="${j.id}">${j.nombre}</option>` });
                result += ` </optgroup> `;
            })
            $('#combo_ambientes').html(result);
        }else{
            $('#combo_ambientes').html("<option value='' selected disabled>No hay datos de ambientes</option>");
            Swal.fire('Error', data.observacion, 'error');
        }
    })
}

function consultarDatosEnergeticos(){
    let edificio = $('#combo_edificio').val();
    let piso = $('#combo_pisos').val();
    let ambiente = $('#combo_ambientes').val();
    // let fechaInicio = $('#fecha_busqueda').val();
    // let fechaFin = $('#fecha_busqueda_fin').val();
    let fechaInicio = $('#reportrange').data('daterangepicker').startDate.format('YYYY-MM-DD');
    let fechaFin = $('#reportrange').data('daterangepicker').endDate.format('YYYY-MM-DD');;

    if(!(edificio || ambiente || piso || fechaInicio || fechaFin)){
        Swal.fire('', 'Se requieren los campos Edificio, Ambientes y Fecha', 'error');
        return;
    }

    informacionConsumo(edificio, piso, ambiente, fechaInicio, fechaFin);
}

function informacionConsumoAnt(edificio, ambiente, fecha){
    dataConsumoAct = undefined;
    dataConsumoFut = undefined;
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
            dataConsumoAct = dataConsumo;
            
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
                console.log(dataConsumo);
                dataConsumoFut = dataConsumo;
                
                chConsumoFut.updateSeries(dataConsumo);

                $('#val_consfut_amb').text(datos['consumo_futuro'][datos['consumo_futuro'].length-1]['Consumo_Mensual'].toFixed(2) + "kWh");
                $('#val_consfut_edi').text(datos['consumo_futuro_total'][datos['consumo_futuro_total'].length-1]['Consumo_Mensual'].toFixed(2) + "kWh");
            }
        }else{
            Swal.fire("", "No se encontro informacion en base a los parametros consultados.", "error");
        }
    })
}
function informacionConsumo(edificio, piso, ambiente, fechaInicio, fechaFin){
    dataConsumoAct = undefined;
    dataConsumoFut = undefined;
   /*let formData = new FormData();
    formData.append('edificio', edificio);
    formData.append('ambiente', ambiente);
    formData.append('fecha', fecha);*/
    
    fetch(rutaAPI+'/datos?idEdificacion='+edificio+'&idPiso='+piso+'&idAmbiente='+ambiente+'&fechaInicio='+fechaInicio+'&fechaFin='+fechaFin, {
        method: 'GET',
    })
    .then(response => response.json())
    .then(data => {
        if(data.ok){
            let datos = data['datos'];
            let consumo_actual = [];
            let consumo_actual_total = [];
            for(let ca of datos['datos']){
                consumo_actual.push({x: ca['fecha'], y: parseFloat(ca['kilovatio'])})
            }

            for(let catotal of datos['datos']){
                consumo_actual_total.push({x: catotal['fecha'], y: parseFloat(catotal['totalKilovatioEdificio'])})
            }
            
            /*let consumo_actual_total = [];
            for(let cat of datos['consumo_actual_total']){
                consumo_actual_total.push({x: cat['Mes'], y: cat['Consumo_Mensual']})
            }*/
            
            let dataConsumo = [{
                name: "Consumo Actual",
                data: consumo_actual
            }, {
                name: "Consumo Total",
                data: consumo_actual_total
            }];
            console.log(dataConsumo)
            dataConsumoAct = dataConsumo;
            
            chConsumoAct.updateSeries(dataConsumo);

            $('#val_consact_amb').text(parseFloat(datos['consumoAmbiente']['kilovatio']).toFixed(2) + "kWh");
            $('#val_consact_edi').text(parseFloat(datos['consumoEdificio']).toFixed(2) + "kWh");

            if(datos['datos'].length > 0){
                predecirConsumo(datos['datos']);
            }else{
                chConsumoFut.updateSeries([
                    {
                        name: "Consumo Futuro",
                        data: consumo_futuro
                    }, {
                        name: "Consumo Futuro Total",
                        data: consumo_futuro_total
                    }
                ]);
            }
            //$('#val_consact_edi').text(datos['consumo_actual_total'][datos['consumo_actual_total'].length-1]['Consumo_Mensual'] + "kWh");
        }else{
            Swal.fire('Error', data.observacion, 'error');
        }
    })
}

function predecirConsumo(datos){
    /*let formData = new FormData();
    formData.append('datos', datos);*/
    dataConsumoFut = undefined;

    fetch('/api/prediccion_datos', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(datos)
    })
    .then(response => response.json())
    .then(data => {
        if(data.ok){
            let datos = data['datos'];
            let consumo_futuro = [];
            let consumo_futuro_total = [];
            //let consumo_actual_total = [];
            for(let cf of datos){
                consumo_futuro.push({x: cf['fecha'], y: parseFloat(cf['consumo_predicho'])})
                consumo_futuro_total.push({x: cf['fecha'], y: parseFloat(cf['consumo_total'])})
            }
            
            /*for(let catotal of datos['datos']){
                consumo_actual_total.push({x: catotal['fecha'], y: parseFloat(catotal['totalKilovatioEdificio'])})
            }*/
            
            
            let dataConsumo = [{
                name: "Consumo Futuro",
                data: consumo_futuro
            }, {
                name: "Consumo Futuro Total",
                data: consumo_futuro_total
            }];

            console.log(dataConsumo)
            dataConsumoFut = dataConsumo;
                
            chConsumoFut.updateSeries(dataConsumo);
            
            let valorConsFuturoAmb = consumo_futuro.reduce((acumulador, consumo) => {
                return acumulador + consumo.y;
            }, 0);  // El valor inicial es 0

            let valorConsFuturoEdi = consumo_futuro_total.reduce((acumulador, consumo) => {
                return acumulador + consumo.y;
            }, 0);  // El valor inicial es 0
            
            //console.log("La suma de los precios es:", sumaPrecios);
            $('#val_consfut_amb').text(valorConsFuturoAmb.toFixed(2) + "kWh");
            $('#val_consfut_edi').text(valorConsFuturoEdi.toFixed(2) + "kWh");
            //chConsumoAct.updateSeries(dataConsumo);
        }else{
            Swal.fire('Ocurrio un error al consultar la informacion.', '', 'error');
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
            //let txtInicio = "Presentate ante el usuario y dale una bienvenida. Tienes que preguntarle al usuario sobre su nombre y si es estudiante o docente.";
            let txtInicio = "Hola.";
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
        "deshabilitado-asistente",
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
        case 'deshabilitado-asistente':
        {
            $('#inner-wave').addClass(animacion);
            $('#icon_control').html('<i class="fa-solid fa-play"></i>');
            $('#icon_control').attr('title', 'Esperando...');
            $('#inner-wave').attr('disabled', true);
        }
        break;
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
            if(dataConsumoAct && dataConsumoFut){
                permiteGraficaClic = false;
            }
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
            
            if(dataConsumoAct && dataConsumoFut){
                permiteGraficaClic = true;
            }else{
                permiteGraficaClic = false;
            }

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
    const maxLength = 190; // entre 190 y 220
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
            let rMensaje = limpiarMensaje(respuesta['respuesta_msg'])
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

//Aqui se iran agregando otros tipos de formateo para darle mas naturalidad al hablar el asistente
function limpiarMensaje(mensaje){
    let sinasteriscos = mensaje.replaceAll('*', ''); //Quita los doble asterisco del texto
    let sinsaltos = sinasteriscos.replaceAll('\n', ''); //Quita los saltos de linea \n del texto
    return sinsaltos; //retorna el texto limpio
}

async function ejecutarFuncion(asisFunciones){
    console.log(asisFunciones);
    let handleAFunciones = {
        'get_usuario': getDatosUsuario,
        'get_ambiente_edificio': getAmbienteEdificio,
        //'get_edificios': mostrarInfoEdificios,
        'get_recomendaciones': getRecomendaciones,
        'get_ids_edificio_piso_ambiente': getInfoLugar,
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

async function getInfoLugar(respuesta){
    let fArgumentos = respuesta['funcion_args'];

    if(fArgumentos['idEdificio'] && fArgumentos['idPiso'] && fArgumentos['idAmbiente']){
        return JSON.stringify({success: true}); 
    }else if(fArgumentos['idEdificio'] || fArgumentos['idPiso'] || fArgumentos['idAmbiente']){
        let arregloText = [];

        if(fArgumentos['idEdificio']) arregloText.push(" el edificio")
        if(fArgumentos['idPiso']) arregloText.push(" el piso")
        if(fArgumentos['idAmbiente']) arregloText.push(" el ambiente")
        
        return "Pidele al usuario que te indique" + arregloText.join(',')+".";
    }else{
        return "Vuelve a preguntarle al usuario por los datos del edificio, el piso y el ambiente";
    }
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
                    $('#select_param_click').hide();
                    $('#select_param_voz').show();
                    $('#combo_edificio_v').val(fArgumentos['edificio']);
                    $('#combo_ambientes_v').val(fArgumentos['ambiente']);
                    $('#fecha_busqueda_v').val('2024-01-10');
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

async function getRecomendaciones(respuesta){
    let fArgumentos = respuesta['funcion_args'];
    $('#txtarea_recomendaciones').val(fArgumentos['recomendaciones']);
    document.querySelector("#txtarea_recomendaciones").scrollIntoView({ behavior: 'smooth' });
    return "Informale al usuario que se ha porporcionado la informacion sobre las recomendaciones";
}

/*async function mostrarInfoEdificios(respuesta){
    let fArgumentos = respuesta['funcion_args'];

    $('#modalInfoEdificios').modal('show');
    
    return "Informale al usuario que se esta mostrando la informacion de los edificios y sus ambientes";
}*/

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

function crearChart(elemento, tipo, nombre){
    let options = {
        chart: {
            type: tipo,
            height: '100%',
            width: '100%',
            toolbar: {
                show: false
            },
            events: {
                markerClick: function(event, chartContext, {seriesIndex, dataPointIndex, w}){
                    let indiceSerie = dataPointIndex;
                    if(permiteGraficaClic){
                        if(dataConsumoAct && nombre == 'grafica_actual'){
                            let lblConsActAmb = dataConsumoAct[0].data[indiceSerie].y;
                            let lblConsActEdi = dataConsumoAct[1].data[indiceSerie].y;
                            $('#val_consact_amb').text(lblConsActAmb+"kWh");
                            $('#val_consact_edi').text(lblConsActEdi+"kWh");
                            conversacion.push({'role': 'user', 'content': 'Mencionale al usuario que el valor actual de consumo de energia del ambiente es  de '+lblConsActAmb+'kWh, y el valor actual del consumo energetico del edificio es de '+lblConsActEdi+'kWh.'});
                            cambiaAnimacionAsistente("cargando-asistente");
                            conversarAsistente();
                        }else if(dataConsumoFut && nombre == 'grafica_futuro'){
                            let lblConsFutAmb = dataConsumoFut[0].data[indiceSerie].y;
                            let lblConsFutEdi = dataConsumoFut[1].data[indiceSerie].y;
                            $('#val_consfut_amb').text(lblConsFutAmb+"kWh");
                            $('#val_consfut_edi').text(lblConsFutEdi+"kWh");
                            conversacion.push({'role': 'user', 'content': 'Mencionale al usuario que el valor futuro de consumo de energia del ambiente es  de '+lblConsFutAmb+'kWh, y el valor futuro del consumo energetico del edificio es de '+lblConsFutEdi+'kWh.'});
                            cambiaAnimacionAsistente("cargando-asistente");
                            conversarAsistente();
                        }else{
                            $('#val_consact_amb').text("0kWh");
                            $('#val_consact_edi').text("0kWh");
                            $('#val_consfut_amb').text("0kWh");
                            $('#val_consfut_edi').text("0kWh");
                            Swal.fire('No existe informacion', '', 'error');
                        }
                    }
                }
            }
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