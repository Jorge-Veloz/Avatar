/*
    Autor del código: Teddy Alejandro Moreira Vélez
    Descripción: Script de funcionamiento de interacciones del asistente e interfaz
    Fecha de creación: 14-10-2024
    Fecha de actualización: 18-10-2024
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

var estadoAsistente = "detenido"; // cambiar a detenido
var asistenteFinalizo = false;
var conversacion = []; // Guardara el historial de conversacion

const urlParams = new URLSearchParams(window.location.search);
var recognition;
var utterance;
var synth;
var voces;

//Inicializacion de los servicios
document.addEventListener("DOMContentLoaded", () => {
    /* ========================== Seteo Reconocimiento de Voz ========================== */
    recognition = new webkitSpeechRecognition();
    recognition.lang = 'es-ES';
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onaudiostart = (event) => {
        //cambiaAnimacionAsistente("iw-hearing");
        estadoAsistente = "escuchando";
    }
    recognition.onaudioend = (event) => {
        //cambiaAnimacionAsistente("iw-loading");
        estadoAsistente = "detenido";
    }
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
    
        conversacion.push({"role": "user", "content": transcript});
        conversarAsistente();
    };
    recognition.onerror = (event) => {
        Swal.fire("Error al reconocer la voz", "Error: "+event.error, "error");
        //cambiaAnimacionAsistente("estatica");
        estadoAsistente = "esperando";
    };
    /* ========================== Fin Seteo Reconocimiento de Voz ========================== */

    /* ========================== Seteo Reproduccion de Voz ========================== */
    utterance = new SpeechSynthesisUtterance(); // Reproducira voz en base a texto
    utterance.lang = 'es-ES' || 'es-MX' || 'es-US' || 'en-US';
    /* ========================== Fin Seteo Reproduccion de Voz ========================== */

    /* ========================== Seteo Charts ========================== */
    setearCharts();
    /* ========================== Fin Seteo Charts ========================== */
});

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

function crearChart(elemento, tipo, data){
    let options = {
        chart: {
            type: tipo,
            height: '100%',
            width: '100%'
        },
        series: data,
        xaxis: {
            categories: [1991,1992,1993,1994,1995,1996,1997, 1998,1999]
        }
    }
    
    let chart = new ApexCharts(elemento, options);
    
    chart.render();

    return chart;
}