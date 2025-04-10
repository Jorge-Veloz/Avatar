    /*
        Autor del código: Teddy Alejandro Moreira Vélez
        Descripción: Script de funcionamiento de interacciones del asistente e interfaz
        Fecha de creación: 14-10-2024
        Fecha de actualización: 03-11-2024
    */
const Index = (function() {
    
    //let vAsistente;
    let estadoAsistente;
    let asistenteFinalizo = false;
    let conversacion = [];
    let gMensaje = "";
    var estadoVoz = "activo";

    var catalogoEdificios;
    let resolverPromAutor;
    let rechazarPromAutor;

    let recognition;
    let utterance;
    let synth;
    let voces;
    let intervalo;
    const TIEMPO_CORTE = 2;
    const rutaAPI = "http://192.168.100.18:3000/v1/asistente-virtual";

    let chConsumoAct;
    let chConsumoFut;
    let dataConsumoAct;
    let dataConsumoFut;
    let permiteGraficaClic = false;

    let dataEdificios = [];
    let fechaInicio;
    let fechaFin;
    let chart1 = null, chart2 = null;

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

    document.addEventListener("DOMContentLoaded", async () => {

        await initGraficos();
        
        if(localStorage.getItem('autorizacion') == 1){
            inicializarDOM();
        }else{
            $('#modal_autorizacion').modal('show');
            //await verificarAutorizacion()
            /*.then((res)=>{
                $('#modal_autorizacion').modal('hide');
                localStorage.setItem('autorizacion', 1);
                inicializarDOM();
                })
                .catch((err) =>{
                    console.log("Ocurrio un error")
                    localStorage.setItem('autorizacion', 0);
                    //location.href = "https://www.google.com/";
                    });*/
        }
                
        $('#rechazar_auto').on('click', () => {clickAutorizacion('R')});
        $('#aceptar_autor').on('click', () => {clickAutorizacion('A')});
        await getEdificios();
    });

    $(function() {
                                        
        var start = moment();
        var end = moment();
    
        function cb(start, end) {
            fechaInicio = start.format('DD/MM/YYYY')
            fechaFin = end.format('DD/MM/YYYY')
            $('#reportrange span').html(start.format('DD MMM YYYY') + ' - ' + end.format('DD MMM YYYY'));
        }
    
        $('#reportrange').daterangepicker({
            startDate: start,
            endDate: end,
            ranges: {
                'Hoy': [moment(), moment()],
                'Ayer': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
                'Últimos 7 días': [moment().subtract(6, 'days'), moment()],
                'Últimos 30 días': [moment().subtract(29, 'days'), moment()],
                'Este mes': [moment().startOf('month'), moment().endOf('month')],
                'Último mes': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
            }
        }, cb);
    
        cb(start, end);
    
    });

    $('#btnVoz').on('click', toggleVoz);

    $('#combo_edificio').on('change', function() {
        let idEdificio = $(this).val();
        let pisos = dataEdificios.find(e => e.id == idEdificio).pisos;
        let ops = "<option value='' selected disabled>Seleccionar</option>";
        for(let p of pisos){
            ops += `<option value='${p.id}'>${p.nombre}</option>`;
        }
        $('#combo_pisos').html(ops);
    });

    $('#combo_pisos').on('change', function() {
        let idPiso = $(this).val();
        let ambientes = dataEdificios.find(e => e.pisos.find(p => p.id == idPiso)).pisos.find(p => p.id == idPiso).ambientes;
        let ops = "<option value='' selected disabled>Seleccionar</option>";
        
        groupBy(ambientes, 'tipoAmbiente').forEach(i => {
            ops += `<optgroup label="${i[0].tipoAmbiente}">`;
            i.forEach(j => { ops += ` <option value="${j.id}">${j.nombre}</option>` });
            ops += ` </optgroup> `;
        })
        $('#combo_ambientes').html(ops);
    });

    $('#btnConsultarDatos').on('click', function() {
        let idEdificio = $('#combo_edificio').val();
        let idPiso = $('#combo_pisos').val();
        let idAmbiente = $('#combo_ambientes').val();
        
        if(idEdificio && idPiso && idAmbiente){
            informacionConsumo({idEdificio, idPiso, idAmbiente});
        }else{
            Swal.fire('Error', 'Seleccione todos los campos.', 'error');
        }
    });

    function inicializarDOM(){
        $('#select_voz').on('change', verificarVoz);
        $('#play_voz').on('click', reproducir);
        $('#guardar_voz').on('click', guardarVocesDefault);
        cambiaAnimacionAsistente('deshabilitado-asistente');
        /* ========================== Seteo Reconocimiento de Voz ========================== */
        recognition = new webkitSpeechRecognition();
        recognition.lang = 'es-ES';
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.onaudiostart = (event) => {
            console.log("Iniciando la escucha");
            if(estadoAsistente && estadoAsistente == "listo"){
                cambiaAnimacionAsistente('detener-asistente')
            }
        }
        recognition.onaudioend = (event) => {
            console.log("Se detuvo la escucha.");
            if(estadoVoz == "activo"){
                //setTimeout(iniciarEscucha, 1000);
                detenerEscucha();
            }
            if(estadoAsistente && estadoAsistente == "listo"){
                cambiaAnimacionAsistente('hablar-asistente')
            }
        }
        recognition.onresult = (event) => {
            //cambiaAnimacionAsistente('cargando-asistente');
            let transcripcion = '';
            //let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                if (event.results[i].isFinal) { // Solo procesar resultados finales
                    transcripcion += event.results[i][0].transcript;
                }
            }
            if (transcripcion.trim()) {
                console.log("Texto transcrito: " + transcripcion);
                /*if(estadoAsistente == "escuchando"){
                    toggleEscucha();
                }else{
                    setTimeout(cambiaAnimacionAsistente('cargando-asistente'), 500);
                    estadoAsistente = "detenido";
                    conversarAsistente();
                }*/
                
                if(estadoAsistente && estadoAsistente == "listo"){
                    gMensaje = transcripcion
                    conversarAsistente();
                }
            }
            /*const transcript = event.results[0][0].transcript;
        
            //conversacion.push({"role": "user", "content": transcript});
            gMensaje = transcript;
            conversarAsistente();*/
        };
        recognition.onerror = (event) => {
            Swal.fire("Error al reconocer la voz", "Error: "+event.error, "error");
            if(estadoAsistente && estadoAsistente == "listo"){
                cambiaAnimacionAsistente('hablar-asistente')
            }
            //estadoAsistente = "listo";
            //toggleEscucha();
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
        chConsumoAct = crearChart(document.querySelector("#grafica_cons_act"), 'line', 'grafica_actual');
        chConsumoFut = crearChart(document.querySelector("#grafica_cons_fut"), 'line', 'grafica_futuro');
        /* ========================== Fin Seteo Charts ========================== */
        //$('#fecha_busqueda').val(new Date().toISOString().split('T')[0]);
        $('#asistente-btn').removeAttr('disabled');
        
        //llenarModalInfoEdificios();
    }

    async function initGraficos(params) {

        const colorSuccess = KTUtil.getCssVariableValue('--bs-success');
        const colorInfo = KTUtil.getCssVariableValue('--bs-info');
        const colorWarning = KTUtil.getCssVariableValue('--bs-warning');
        const ColorBsGray500 = KTUtil.getCssVariableValue('--bs-gray-500');
        const labelColor = KTUtil.getCssVariableValue('--bs-gray-500');
        const borderColor = KTUtil.getCssVariableValue('--bs-border-dashed-color');
        
        const element1 = document.getElementById("grafico1");
        const element2 = document.getElementById("grafico2");
        
        let options = {
            noData: {
                text: 'Sin datos',
                align: 'center',
                verticalAlign: 'middle',
                style: {
                    color: labelColor,
                    fontSize: '12px'
                }
            },
            series: [{
                name: 'Consumo actual',
                data: []
            }, {
                name: 'Consumo futuro',
                data: []
            }],
            chart: {
                fontFamily: 'Inter, Roboto, Poppins',
                stacked: true,
                type: 'area',
                height: parseInt(KTUtil.css(element1, 'height')) + 10,
                toolbar: { show: false },
                sparkline: { enabled: false }
            },
            dataLabels: {
                enabled: false
            },
            markers: {
                size: 4,
                colors: undefined, // Usa el color de la serie automáticamente
                strokeColors: undefined, // Contorno negro para visibilidad
                strokeWidth: 0,
                hover: {
                    size: 7 // Aumenta el tamaño al pasar el mouse
                }
            },
            stroke: {
                curve: 'smooth'
            },
            yaxis: {
                show: false
            },
            xaxis: {
                // type: 'datetime',
                categories: []
                // categories: ["2018-09-19T00:00:00.000Z", "2018-09-19T01:30:00.000Z", "2018-09-19T02:30:00.000Z", "2018-09-19T03:30:00.000Z", "2018-09-19T04:30:00.000Z", "2018-09-19T05:30:00.000Z", "2018-09-19T06:30:00.000Z"]
            },
            legend: {
                position: 'top'
            },
            tooltip: {
                x: {
                    format: 'dd MMM yyyy'
                },
            },
        };
    
        chart1 = new ApexCharts(element1, options);
        chart1.render();

        chart2 = new ApexCharts(element2, options);
        chart2.render();
    }

    function llenarModalInfoEdificios(){
        let htmlAcordion = ``;
        let datos = dataEdificios;
    
        if(datos && datos.length > 0){
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

    async function informacionConsumoAsistente(edificio, piso, ambiente, fechaInicio, fechaFin){
        //Revisar si los identificadores son correctos
        let idIncorrecto = false;
        let idsEdificios = getIdsCatalogo();
        [edificio, piso, ambiente].forEach(c => {
            if(!idsEdificios.includes(c)){
                idIncorrecto = true;
            }
        });
    
        if(idIncorrecto){
            return {"success": false, "reason": "Vuelve a analizar el archivo, has obtenido mal los identificadores"}
        }
    
        //Verificar si la informacion coincide (edificio => piso => ambiente)
        let vEdificio = dataEdificios.filter(e => e.id == edificio);
    
        if(!vEdificio || (vEdificio && vEdificio.length <= 0)){
            return {"success": false, "reason": "La informacion que te han proporcionado es erronea. Identificador de edificio no corresponde a ninguno de los edificios del archivo."}
        }else{
            let vPiso = vEdificio[0].pisos.filter(p => p.id == piso);
            
            if(!vPiso || (vPiso && vPiso.length <= 0)){
                return {"success": false, "reason": "La informacion que te han proporcionado es erronea. No existe este piso en el edificio mencionado."}
            }else{
                let vAmbiente = vPiso[0].ambientes.filter(a => a.id == ambiente);
                if(!vAmbiente || (vAmbiente && vAmbiente.length <= 0)){
                    return {"success": false, "reason": "La informacion que te han proporcionado es erronea. No existe este ambiente en el piso mencionado."}
                }
            }
        }
    
        //Verificar existencia de datos con los parametros
        try {
            // Usamos fetch para hacer una solicitud a una API o URL
            const respuesta = await fetch(rutaAPI+'/datos?idEdificacion='+edificio+'&idPiso='+piso+'&idAmbiente='+ambiente+'&fechaInicio='+fechaInicio+'&fechaFin='+fechaFin, {method: 'GET'}); // URL de ejemplo
            if (!respuesta.ok) {
                throw new Error('Error en la respuesta de la API');
            }
            // Esperamos a que se convierta la respuesta en formato JSON
            const datos = await respuesta.json();
            
            $('#combo_edificio').val(edificio);
            $('#combo_pisos').val(piso);
            $('#combo_ambientes').val(ambiente);
            $('#reportrange').daterangepicker({
                locale: {
                    format: 'YYYY-MM-DD' // Establece el formato de fecha
                },
                startDate: fechaInicio,  // Fecha inicial
                endDate: fechaFin,    // Fecha final
                opens: 'center',          // Posición del calendario
            });
    
            if(datos.ok){
                graficarInfoConsumo(datos);
                if(datos['datos']['datos'].length > 0){
                    return {"success": true, "reason": "Obtuviste los datos del consumo energetico, hazle saber al usuario que seran graficados a continuación. Además dale unas recomendaciones para optimizar el consumo energetico del edificio y ambientes."}
                }else{
                    return {"success": true, "reason": "Se realizo correctamente la consulta pero no habian datos de consumo de ese ambiente, hazle saber al usuario"}
                }
            }else{
                return {"success": true, "reason": "Los datos enviados fueron correctos, mas hubo un error a la consulta en la bd. " + datos.observacion}
            }
        } catch (error) {
          console.error('Hubo un error:', error);
        }
    
        //OK: {"success": true, "reason": "Obtuviste los datos del consumo energetico, hazle saber al usuario que seran graficados a continuación"}
    }
    
    function informacionConsumo(params){
        
        /*dataConsumoAct = undefined;
        dataConsumoFut = undefined;*/
        
        $('.text-btn-consultar-datos').html('Consultando datos... <span class="indicator-progress">Cargando... <span class="spinner-border spinner-border-sm align-middle ms-2"></span></span>');
        $('#btnConsultarDatos,select').addClass('disabled');

        fetch(`${rutaAPI}/datos?idEdificacion=${params.idEdificio}&idPiso=${params.idPiso}&idAmbiente=${params.idAmbiente}&fechaInicio=${fechaInicio}&fechaFin=${fechaFin}`, {
            method: 'GET',
        })
        .then(response => response.json())
        .then(result => {

            $('.text-btn-consultar-datos').html('Consultar datos');
            $('#btnConsultarDatos,select').removeClass('disabled');

            if(result.ok){
                graficarInfoConsumo(result)
            }else{
                Swal.fire('Error', result.observacion, 'error');
            }
        }).catch(error => {
            $('.text-btn-consultar-datos').html('Consultar datos');
            $('#btnConsultarDatos,select').removeClass('disabled');
            Swal.fire("Error en el servidor.", "Error: "+error.message, "error");
        });
    }

    function graficarInfoConsumo(result){
        document.querySelector('.consumo-actual-ambiente').innerHTML = result.datos.consumoAmbiente.kilovatio.toLocaleString('es-ES', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });

        document.querySelector('.consumo-actual-edificio').innerHTML = result.datos.consumoEdificio.toLocaleString('es-ES', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
        
        const resultConsumoActualAmbiente = result.datos.datos.map( e => {
            return {
                x: e.fecha,
                y: parseFloat(e.kilovatio)
            }
        }, []);

        const resultConsumoActualEdificio = result.datos.datos.map( e => {
            return {
                x: e.fecha,
                y: parseFloat(e.totalKilovatioEdificio)
            }
        }, []);
        
        const options = {
            series: [{
                name: 'Consumo actual',
                data: resultConsumoActualAmbiente,
                // color: 'var(--bs-success)',
            }, {
                name: 'Consumo futuro',
                data: resultConsumoActualEdificio,
                // color: 'var(--bs-info)',
            }],
        };

        chart1.updateOptions(options)

        predecirConsumo(result.datos.datos);

    }

    function predecirConsumo(datos){
        
        dataConsumoFut = undefined;

        fetch('/api/prediccion_datos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        })
        .then(response => response.json())
        .then(result => {
            if(result.ok){

                const resultConsumoFuturoAmbiente = result.datos.map( e => {
                    return {
                        x: e.fecha,
                        y: Number(e.consumo_predicho.toFixed(2)),
                    }
                }, []);

                const resultConsumoFuturoEdificio = result.datos.map( e => {
                    return {
                        x: e.fecha,
                        y: Number(e.consumo_total.toFixed(2)),
                    }
                }, []);

                let consumoFuturoAmbiente = resultConsumoFuturoAmbiente.reduce((acumulador, consumo) => {
                    return acumulador + consumo.y;
                }, 0);
                
                let consumoFuturoEdificio = resultConsumoFuturoEdificio.reduce((acumulador, consumo) => {
                    return acumulador + consumo.y;
                }, 0);
                
                document.querySelector('.consumo-futuro-ambiente').innerHTML = consumoFuturoAmbiente.toLocaleString('es-ES', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });

                document.querySelector('.consumo-futuro-edificio').innerHTML = consumoFuturoEdificio.toLocaleString('es-ES', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                });
                
                const options = {
                    series: [{
                        name: 'Consumo futuro',
                        data: resultConsumoFuturoAmbiente,
                        // color: 'var(--bs-success)',
                    }, {
                        name: 'Consumo futuro edificio',
                        data: resultConsumoFuturoEdificio,
                        // color: 'var(--bs-info)',
                    }],
                };
                
                chart2.updateOptions(options)

            }else{
                Swal.fire('Ocurrio un error al consultar la informacion.', '', 'error');
            }
        })
    }












    async function verificarAutorizacion(){
        return new Promise((resolve, reject) => {
            resolverPromAutor = resolve;
            rechazarPromAutor = reject;
        })
    }

    
    function clickAutorizacion(accion){
        console.log(accion);
        if(accion == 'A'){
            $('#modal_autorizacion').modal('hide');
            localStorage.setItem('autorizacion', 1);
            inicializarDOM();
            //resolverPromAutor('Autorizacion aceptada');
            /*resolverPromAutor = null;
            rechazarPromAutor = null;*/
        }else{
            location.href = "https://www.google.com/";
        }
    }

    /* TODO: Revisar modales */
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

    /* TODO: Revisar modales */
    function verificarVoz(){
        let vAsis = $('#select_voz').val();
        //console.log(vMasc + vFem);
        if(vAsis){
            $('#guardar_voz').attr('disabled', false);
        }else{
            $('#guardar_voz').attr('disabled', true);
        }
    }

    /* TODO: Revisar modales */
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

    /* TODO: Revisar modales */
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

    /* TODO: Revisar modales */
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

    async function getEdificios(){
        
        $('#combo_edificio,#combo_pisos,#combo_ambientes').html("<option value='0' selected disabled>Cargando...</option>");
        
        await fetch(rutaAPI+'/edificios', {
            method: 'GET'
        })
        .then(response => {
            return response.json();
        })
        .then(result => {
            
            $('#combo_edificio,#combo_pisos,#combo_ambientes').html("<option value='0' selected disabled>Seleccionar</option>");
            
            if(result.ok){
                
                dataEdificios = result.datos;

                let ops = "<option value='' selected disabled>Seleccione el edificio</option>";
                result.datos.forEach(element => {
                    ops += `<option value='${element.id}'>${element.nombre}</option>`;
                });
                $('#combo_edificio').html(ops);
                llenarModalInfoEdificios();
                
            }else{
                $('#combo_edificio,#combo_pisos,#combo_ambientes').html("<option value='0' selected disabled>Seleccionar</option>");
                Swal.fire('Error', result.observacion, 'error');
            }
        })
        .catch(error => {
            Swal.fire("Error en el servidor.", "Error: "+error.message, "error");
        });
    }

    function getIdsCatalogo(){
        let idsEdificios = []
        for(let e of dataEdificios){
            idsEdificios.push(e.id);
            for(let p of e.pisos){
                idsEdificios.push(p.id);
                for(let a of p.ambientes){
                    idsEdificios.push(a.id);
                }
            }
        }
        return idsEdificios;
    }

    function groupBy(arr, prop) {
        const map = new Map(Array.from(arr, obj => [obj[prop],
        []
        ]));
        arr.forEach(obj => map.get(obj[prop]).push(obj));
        return Array.from(map.values());
    }
    
    function inicializarAsistente(){
        if(estadoAsistente) return;
        estadoAsistente = "detenido";
        cambiaAnimacionAsistente("cargando-asistente");
        $('#btnVoz').attr('disabled', true);
        fetch('/inicializar', {
            method: 'GET',
        })
        .then(response => response.json())
        .then(data => {
            asistenteFinalizo = false;
            
            if(data.ok){
                gMensaje = "Presentate ante el usuario y dale una bienvenida. Tienes que preguntarle al usuario sobre su nombre y si es estudiante o docente.";
                //let txtInicio = "Hola.";
                //conversacion.push({'role': 'user', 'content': txtInicio});
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
                estadoAsistente = "listo";
                
                if(dataConsumoAct && dataConsumoFut){
                    permiteGraficaClic = true;
                }else{
                    permiteGraficaClic = false;
                }
                iniciarEscucha();

                // if(asistenteFinalizo){
                //     $('#inner-wave').removeClass('iw-enabled');
                //     guardarFormulario();
                //     estadoAsistente = "detenido";
                // }
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
            console.log("Pause event: " + vBoundary);
        };

        utterance.onboundary = (vPause) => {
            console.log("Boundary event: " + vPause);
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
        }
    }

    function toggleVoz(){
        if(estadoAsistente){
            if(estadoVoz == "activo"){
                detenerEscucha();
            }else if(estadoVoz == "noactivo"){
                iniciarEscucha();
            }
        }else{
            inicializarAsistente();
        }
        //toggleEscucha()
    }

    function iniciarEscucha(){
        $('#btnMicInit').hide();
        $('#btnMicStop').hide();
        $('#btnMicUp').show();
        estadoVoz = "activo";
        recognition.start();
    }

    function detenerEscucha(){
        $('#btnMicInit').hide();
        $('#btnMicUp').hide();
        $('#btnMicStop').show();
        estadoVoz = "noactivo";
        recognition.stop();
    }

    // hace posible la conversacion con el asistente
    function conversarAsistente(){
        cambiaAnimacionAsistente('cargando-asistente');
        estadoAsistente = "detenido";

        const formData = new FormData();
        formData.append('mensaje', gMensaje);

        fetch('/conversar', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {

            if(data.ok){
                let respuesta = data['datos'];
                if(!$('#contenedor-typing').hasClass('ct-appear')){
                    $('#contenedor-typing').addClass('ct-appear');
                }
                //conversacion = [];
                gMensaje = "";
                if(respuesta['asis_funciones']){
                    ejecutarFuncion(respuesta['asis_funciones'], respuesta['id_run']);
                    //console.log(respuesta);
        
                }else if(respuesta['respuesta_msg']){
                    let textType = document.getElementById('typeContenido');
                    let rMensaje = limpiarMensaje(respuesta['respuesta_msg'])
                    let iTextChar = 0;
        
                    //TODO: Se implementara despues
                    /*textType.textContent = "";
                    idInt = setInterval(() => {
                        if (iTextChar < rMensaje.length) {
                            textType.textContent += rMensaje.charAt(iTextChar);
                            iTextChar++;
                        }else{
                            clearInterval(idInt);
                        }
                    }, 55);*/

                    console.log(rMensaje);
                    hablar(rMensaje);
                    //conversacion.push({"role": "assistant", "content": rMensaje});
                    //gMensaje = rMensaje;
                }
            }
        });
    }

    //Aqui se iran agregando otros tipos de formateo para darle mas naturalidad al hablar el asistente
    function limpiarMensaje(mensaje){
        let sinasteriscos = mensaje.replaceAll('*', ''); //Quita los doble asterisco del texto
        let sinsaltos = sinasteriscos.replaceAll('\n', ' '); //Quita los saltos de linea \n del texto
        return sinsaltos; //retorna el texto limpio
    }

    async function ejecutarFuncion(asisFunciones, idRun){
        console.log(asisFunciones);
        let handleAFunciones = {
            'get_usuario': getDatosUsuario,
            'get_ambiente_edificio': getAmbienteEdificio,
            //'get_edificios': mostrarInfoEdificios,
            'get_recomendaciones': getRecomendaciones,
            'get_ids_edificio_piso_ambiente': getInfoLugar,
        }

        let respuestaFunciones = []

        for(let afuncion of asisFunciones){
            //afuncion['funcion']
            //afuncion['funcion_args'] = JSON.parse(afuncion['funcion_args']);
            //console.log(afuncion);
            const activarFuncion = handleAFunciones[afuncion['funcion_name']];

            let rcontent = await activarFuncion(afuncion);
            let respuestaF = {
                "tool_call_id": afuncion['funcion_id'],
                "output": rcontent['reason']
            };
            //conversacion.push(respuestaF);
            respuestaFunciones.push(respuestaF);
        }
        enviarFunciones(respuestaFunciones, idRun);
    }

    function enviarFunciones(respuestaFunciones, idRun){
        const formData = new FormData();
        formData.append('toolcall_output', JSON.stringify(respuestaFunciones));
        formData.append('id_run', idRun);

        //console.log(conversacion);

        fetch('/enviar-funciones', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {

            if(data.ok){
                let respuesta = data['datos'];
                if(!$('#contenedor-typing').hasClass('ct-appear')){
                    $('#contenedor-typing').addClass('ct-appear');
                }
                //conversacion = [];
                gMensaje = "";
                if(respuesta['asis_funciones']){
                    ejecutarFuncion(respuesta['asis_funciones'], respuesta['id_run']);
                    //console.log(respuesta);
        
                }else if(respuesta['respuesta_msg']){
                    let textType = document.getElementById('typeContenido');
                    let rMensaje = limpiarMensaje(respuesta['respuesta_msg'])
                    let iTextChar = 0;
        
                    /*textType.textContent = "";
                    idInt = setInterval(() => {
                        if (iTextChar < rMensaje.length) {
                            textType.textContent += rMensaje.charAt(iTextChar);
                            iTextChar++;
                        }else{
                            clearInterval(idInt);
                        }
                    }, 55);*/
                    console.log(rMensaje);
                    hablar(rMensaje);
                    //conversacion.push({"role": "assistant", "content": rMensaje});
                    gMensaje = rMensaje;
                }
            }
        });
    }

    async function getInfoLugar(respuesta){
        let fArgumentos = respuesta['funcion_args'];

        if(fArgumentos['idEdificio'] && fArgumentos['idPiso'] && fArgumentos['idAmbiente'] && fArgumentos['fechaInicio'] && fArgumentos['fechaFin']){
            let respuesta = await informacionConsumoAsistente(fArgumentos['idEdificio'], fArgumentos['idPiso'], fArgumentos['idAmbiente'], fArgumentos['fechaInicio'], fArgumentos['fechaFin']);
            //console.log(fArgumentos['idEdificio'], fArgumentos['idPiso'], fArgumentos['idAmbiente'], '2024-06-01', '2024-06-30');
            // En caso de datos erroneos aplicar a consulta: {"success": false, "reason": "Vuelve a analizar el archivo, has obtenido mal los identificadores"}
            //return JSON.stringify({"success": true}); 
            return respuesta; 
        }else if(fArgumentos['idEdificio'] || fArgumentos['idPiso'] || fArgumentos['idAmbiente']){
            /*let arregloText = [];

            if(fArgumentos['idEdificio']) arregloText.push(" el edificio")
            if(fArgumentos['idPiso']) arregloText.push(" el piso")
            if(fArgumentos['idAmbiente']) arregloText.push(" el ambiente")
            
            return {"error": "Pidele al usuario que te indique" + arregloText.join(',')+"."};*/
            return {"success": false, "reason": "No tienes la informacion completa para poder consultar el consumo energetico"}
        }else{
            return {"success": false, "reason": "Necesitas todos los datos para poder consultar el consumo energetico"};
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
        return {"success": false, "reason": "Informale al usuario que se ha porporcionado la informacion sobre las recomendaciones"}
    }

    /*async function mostrarInfoEdificios(respuesta){
        let fArgumentos = respuesta['funcion_args'];

        $('#modalInfoEdificios').modal('show');
        
        return "Informale al usuario que se esta mostrando la informacion de los edificios y sus ambientes";
    }*/

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
                                //conversacion.push({'role': 'user', 'content': 'Mencionale al usuario que el valor actual de consumo de energia del ambiente es  de '+lblConsActAmb+'kWh, y el valor actual del consumo energetico del edificio es de '+lblConsActEdi+'kWh.'});
                                gMensaje = 'Mencionale al usuario que el valor actual de consumo de energia del ambiente es  de '+lblConsActAmb+'kWh, y el valor actual del consumo energetico del edificio es de '+lblConsActEdi+'kWh.'
                                cambiaAnimacionAsistente("cargando-asistente");
                                conversarAsistente();
                            }else if(dataConsumoFut && nombre == 'grafica_futuro'){
                                let lblConsFutAmb = dataConsumoFut[0].data[indiceSerie].y;
                                let lblConsFutEdi = dataConsumoFut[1].data[indiceSerie].y;
                                $('#val_consfut_amb').text(lblConsFutAmb+"kWh");
                                $('#val_consfut_edi').text(lblConsFutEdi+"kWh");
                                //conversacion.push({'role': 'user', 'content': 'Mencionale al usuario que el valor futuro de consumo de energia del ambiente es  de '+lblConsFutAmb+'kWh, y el valor futuro del consumo energetico del edificio es de '+lblConsFutEdi+'kWh.'});
                                gMensaje = 'Mencionale al usuario que el valor futuro de consumo de energia del ambiente es  de '+lblConsFutAmb+'kWh, y el valor futuro del consumo energetico del edificio es de '+lblConsFutEdi+'kWh.'
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

})();