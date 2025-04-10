/*
 * Autor: Teddy Alejandro Moreira Vélez
 * Optimized and Organized Code - Stéfano Solintecom Project
 * Creado: 14-10-2024 | Última actualización: 03-11-2024
 */
 
(function() {
    'use strict';
  
    // ============================== Constantes y Configuración ==============================
    const TIEMPO_CORTE = 2;
    //const rutaAPI = "http://localhost:3000/v1/asistente-virtual";
    const rutaAPI = "http://192.168.100.18:3000/v1/asistente-virtual";
    const errorChromeMsg = `<a href="https://www.google.com/intl/es-419/chrome/">Se recomienda usar Chrome</a>`;
    const errorEdgeMsg = `<a href="https://www.microsoft.com/es-es/edge/download">Edge</a>`;
  
    // ============================== Variables de Estado ==============================
    let estadoAsistente,
        estadoVoz = "activo",
        asistenteFinalizo = false,
        permiteGraficaClic = false,
        gMensaje = "";
    let conversacion = [];
    let dataEdificios = [];
    let fechaInicio, fechaFin;
    let chConsumoAct, chConsumoFut, dataConsumoAct, dataConsumoFut;
    let chart1 = null, chart2 = null;
    let recognition, utterance, synth, voces;
    let intervalo;
    let resolverPromAutor, rechazarPromAutor;
  
    // ============================== Inicialización General ==============================
    $(document).ready(async function() {
      initMicrofono();
      initConsentimiento();
      initFechas();
      initGraficos();
      await getEdificios();
      bindUIEvents();
    });
  
    // ------------------------------ Funciones de Inicialización ------------------------------
    function initMicrofono() {
      if (!window.webkitSpeechRecognition) {
        Swal.fire({
          title: "Error",
          text: "Su navegador no soporta el reconocimiento de voz.\nIntente con otro navegador",
          icon: "error",
          showConfirmButton: false,
          allowOutsideClick: false,
          footer: errorChromeMsg
        });
        disableFormControls();
      }
      if (!window.SpeechSynthesisUtterance) {
        Swal.fire({
          title: "Error",
          text: "Su navegador no soporta el intérprete de texto a voz.\nIntente con otro navegador",
          icon: "error",
          showConfirmButton: false,
          allowOutsideClick: false,
          footer: errorChromeMsg
        });
        disableFormControls();
      }
      if (!window.SpeechSynthesis) {
        Swal.fire({
          title: "Error",
          text: "Su navegador no soporta la reproducción de voz.\nIntente con otro navegador",
          icon: "error",
          showConfirmButton: false,
          allowOutsideClick: false,
          footer: `<em>Se recomienda usar ${errorChromeMsg} o ${errorEdgeMsg}</em>`
        });
        disableFormControls();
      }
    }
  
    function disableFormControls() {
      $('#cod-form').attr('disabled', 'true');
      $('#fecha_atencion').attr('disabled', 'true');
    }
  
    function initConsentimiento() {
      if (localStorage.getItem('autorizacion') == 1) {
        inicializarDOM();
      } else {
        $('#modal_autorizacion').modal('show');
      }
      $('#rechazar_auto').on('click', () => clickAutorizacion('R'));
      $('#aceptar_autor').on('click', () => clickAutorizacion('A'));
    }
  
    function initFechas() {
      const start = moment();
      const end = moment();
      const cb = function(start, end) {
        fechaInicio = start.format('YYYY-MM-DD');
        fechaFin = end.format('YYYY-MM-DD');
        $('#reportrange span').html(`${start.format('DD MMM YYYY')} - ${end.format('DD MMM YYYY')}`);
      };
  
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
    }
  
    function initGraficos() {
      const colorVars = {
        success: KTUtil.getCssVariableValue('--bs-success'),
        info: KTUtil.getCssVariableValue('--bs-info'),
        warning: KTUtil.getCssVariableValue('--bs-warning'),
        gray: KTUtil.getCssVariableValue('--bs-gray-500'),
        border: KTUtil.getCssVariableValue('--bs-border-dashed-color')
      };
  
      const chartOptions = {
        noData: {
          text: 'Sin datos',
          align: 'center',
          verticalAlign: 'middle',
          style: { color: colorVars.gray, fontSize: '12px' }
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
          type: 'area',
          height: parseInt(KTUtil.css($('#grafico1')[0], 'height')) + 10,
          toolbar: { show: false },
          sparkline: { enabled: false }
        },
        dataLabels: { enabled: false },
        markers: { size: 4, hover: { size: 7 } },
        stroke: { curve: 'smooth' },
        yaxis: { show: false },
        xaxis: { 
          categories: [],
          labels: {
            formatter: function(value) {
              return moment(value).format('DD MMM YYYY'); // Formatea la fecha
            }
          }
        },
        legend: { position: 'top' },
        tooltip: { 
          x: { format: 'dd MMM yyyy' },
          y: {
            formatter: function(value) {
              return `${value.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} W`; // Agrega 'W' a los valores
            }
          }
        }
      };
  
      chart1 = new ApexCharts(document.querySelector("#grafico1"), chartOptions);
      chart1.render();
      chart2 = new ApexCharts(document.querySelector("#grafico2"), chartOptions);
      chart2.render();

    }
  
    function bindUIEvents() {
      $('#btnVoz').on('click', toggleVoz);
      $('#combo_edificio').on('change', onEdificioChange);
      $('#combo_pisos').on('change', onPisoChange);
      $('#btnConsultarDatos').on('click', function() {
        const idEdificio = $('#combo_edificio').val();
        const idPiso = $('#combo_pisos').val();
        const idAmbiente = $('#combo_ambientes').val();
        if (idEdificio && idPiso && idAmbiente) {
          informacionConsumo({ idEdificio, idPiso, idAmbiente });
        } else {
          Swal.fire('Error', 'Seleccione todos los campos.', 'error');
        }
      });
      $('#select_voz').on('change', verificarVoz);
      $('#play_voz').on('click', reproducir);
      $('#guardar_voz').on('click', guardarVocesDefault);
    }
  
    // ------------------------------ Eventos de Selección ------------------------------
    function onEdificioChange(event) {
      const idEdificio = event.target.value;
      const edificio = dataEdificios.find(e => e.id == idEdificio);
      if (edificio) {
        let ops = "<option value='' selected disabled>Seleccionar</option>";
        edificio.pisos.forEach(p => ops += `<option value='${p.id}'>${p.nombre}</option>`);
        $('#combo_pisos').html(ops);
      }
    }
  
    function onPisoChange(event) {
      const idPiso = event.target.value;
      const pisoData = dataEdificios.find(e => e.pisos.find(p => p.id == idPiso));
      const piso = pisoData?.pisos.find(p => p.id == idPiso);
      if (piso) {
        let ops = "<option value='' selected disabled>Seleccionar</option>";
        groupBy(piso.ambientes, 'tipoAmbiente').forEach(group => {
          ops += `<optgroup label="${group[0].tipoAmbiente}">`;
          group.forEach(item => ops += `<option value="${item.id}">${item.nombre}</option>`);
          ops += `</optgroup>`;
        });
        $('#combo_ambientes').html(ops);
      }
    }
  
    // ============================== Inicialización del DOM para Voz y Asistente ==============================
    async function inicializarDOM() {
      $('#select_voz').on('change', verificarVoz);
      $('#play_voz').on('click', reproducir);
      $('#guardar_voz').on('click', guardarVocesDefault);
  
      // Configurar reconocimiento de voz
      recognition = new webkitSpeechRecognition();
      recognition.lang = 'es-ES';
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.onaudiostart = function() {
        console.log("Iniciando la escucha");
        // Se remueven las llamadas a la animación
      };
      recognition.onaudioend = function() {
        console.log("Se detuvo la escucha.");
        if (estadoVoz === "activo") {
          detenerEscucha();
        }
      };
      recognition.onresult = function(event) {
        let transcripcion = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) transcripcion += event.results[i][0].transcript;
        }
        if (transcripcion.trim() && estadoAsistente === "listo") {
          console.log("Texto transcrito: " + transcripcion);
          gMensaje = transcripcion;
          conversarAsistente();
        }
      };
      recognition.onerror = function(event) {
        Swal.fire("Error al reconocer la voz", "Error: " + event.error, "error");
      };
  
      // Configurar síntesis de voz
      utterance = new SpeechSynthesisUtterance();
      synth = window.speechSynthesis;
      gestionarErrorVoz();
      if (/Android|iPhone|iPad/i.test(navigator.userAgent)) {
        utterance.lang = 'es-ES';
      } else if (/Macintosh/i.test(navigator.userAgent)) {
        synth.addEventListener("voiceschanged", function() { setearVoces(); });
      } else {
        synth.onvoiceschanged = setearVoces;
      }
      $('#asistente-btn').removeAttr('disabled');
    }
  
    // ============================== Funciones para Llamadas a la API y Gestión de Datos ==============================
    async function getEdificios() {
      $('#combo_edificio, #combo_pisos, #combo_ambientes').html("<option value='0' selected disabled>Cargando...</option>");
      try {
        const response = await fetch(`${rutaAPI}/edificios`);
        const result = await response.json();
        $('#combo_edificio, #combo_pisos, #combo_ambientes').html("<option value='0' selected disabled>Seleccionar</option>");
        if (result.ok) {
          dataEdificios = result.datos;
          let ops = "<option value='' selected disabled>Seleccione el edificio</option>";
          result.datos.forEach(element => ops += `<option value='${element.id}'>${element.nombre}</option>`);
          $('#combo_edificio').html(ops);
          llenarModalInfoEdificios();
        } else {
          Swal.fire('Error', result.observacion, 'error');
        }
      } catch (error) {
        Swal.fire("Error en el servidor.", "Error: " + error.message, "error");
      }
    }
  
    function llenarModalInfoEdificios() {
      let htmlAcordion = "";
      if (Array.isArray(dataEdificios) && dataEdificios.length > 0) {
        dataEdificios.forEach((edificio, indexEdi) => {
          htmlAcordion += `
            <div class="accordion-item">
              <h2 class="accordion-header" id="flush-headingEdificios${indexEdi}">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseEdificios${indexEdi}" aria-expanded="false" aria-controls="flush-collapseEdificios${indexEdi}">
                  ${edificio.nombre}
                </button>
              </h2>
              <div id="flush-collapseEdificios${indexEdi}" class="accordion-collapse collapse" aria-labelledby="headingEdificios${indexEdi}" data-bs-parent="#accordionFlushExample">
                <div class="accordion-body p-0 ps-3">
          `;
          if (edificio.pisos && edificio.pisos.length > 0) {
            htmlAcordion += `<div class="accordion accordion-flush" id="accordionFlushExampleEdificio${indexEdi}">`;
            edificio.pisos.forEach((piso, indexPiso) => {
              htmlAcordion += `
                <div class="accordion-item">
                  <h2 class="accordion-header" id="flush-headingPiso${indexPiso}">
                    <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapsePiso${indexPiso}" aria-expanded="false" aria-controls="flush-collapsePiso${indexPiso}">
                      ${piso.nombre}
                    </button>
                  </h2>
                  <div id="flush-collapsePiso${indexPiso}" class="accordion-collapse collapse" aria-labelledby="flush-headingPiso${indexPiso}" data-bs-parent="#accordionFlushExampleEdificio${indexEdi}">
                    <div class="accordion-body p-0 ps-3">
              `;
              if (piso.ambientes && piso.ambientes.length > 0) {
                htmlAcordion += `<ul class="list-group list-group-flush">`;
                piso.ambientes.forEach(ambiente => htmlAcordion += `<li class="list-group-item">${ambiente.nombre}</li>`);
                htmlAcordion += `</ul>`;
              }
              htmlAcordion += `</div></div></div>`;
            });
            htmlAcordion += `</div>`;
          }
          htmlAcordion += `</div></div></div>`;
        });
      }
      $('#accordionFlushExample').html(htmlAcordion);
    }
  
    function getIdsCatalogo() {
      const ids = [];
      dataEdificios.forEach(e => {
        ids.push(e.id);
        e.pisos.forEach(p => {
          ids.push(p.id);
          p.ambientes.forEach(a => ids.push(a.id));
        });
      });
      return ids;
    }
  
    async function informacionConsumoAsistente(edificio, piso, ambiente, fechaInicio, fechaFin) {
      if (!dataEdificios.length) return { success: false, reason: "Error de conexión con la base de datos." };
      const idsEdificios = getIdsCatalogo();
      if (![edificio, piso, ambiente].every(c => idsEdificios.includes(c))) {
        return { success: false, reason: "Los identificadores obtenidos son incorrectos." };
      }
      const vEdificio = dataEdificios.find(e => e.id == edificio);
      if (!vEdificio) return { success: false, reason: "Identificador de edificio incorrecto." };
      const vPiso = vEdificio.pisos.find(p => p.id == piso);
      if (!vPiso) return { success: false, reason: "El piso no existe en el edificio mencionado." };
      const vAmbiente = vPiso.ambientes.find(a => a.id == ambiente);
      if (!vAmbiente) return { success: false, reason: "El ambiente no existe en el piso mencionado." };
  
      try {
        const response = await fetch(`${rutaAPI}/datos?idEdificacion=${edificio}&idPiso=${piso}&idAmbiente=${ambiente}&fechaInicio=${fechaInicio}&fechaFin=${fechaFin}`);
        if (!response.ok) throw new Error('Error en la API');
        const datos = await response.json();
        $('#combo_edificio').val(edificio);
        $('#combo_pisos').val(piso);
        $('#combo_ambientes').val(ambiente);
        $('#reportrange').daterangepicker({
          locale: { format: 'YYYY-MM-DD' },
          startDate: fechaInicio,
          endDate: fechaFin,
          opens: 'center'
        });
        if (datos.ok) {
          graficarInfoConsumo(datos);
          return datos.datos.datos.length > 0
            ? { success: true, reason: "Datos del consumo energético obtenidos. Se graficarán y se darán recomendaciones para optimizar." }
            : { success: true, reason: "Consulta realizada correctamente, pero no se encontraron datos de consumo para el ambiente." };
        } else {
          return { success: true, reason: "Error en la consulta: " + datos.observacion };
        }
      } catch (error) {
        console.error('Error:', error);
      }
    }
  
    function informacionConsumo(params) {
      $('.text-btn-consultar-datos').html('Consultando datos... <span class="indicator-progress">Cargando... <span class="spinner-border spinner-border-sm align-middle ms-2"></span></span>');
      $('#btnConsultarDatos, select').addClass('disabled');
      fetch(`${rutaAPI}/datos?idEdificacion=${params.idEdificio}&idPiso=${params.idPiso}&idAmbiente=${params.idAmbiente}&fechaInicio=${fechaInicio}&fechaFin=${fechaFin}`)
        .then(response => response.json())
        .then(result => {
          $('.text-btn-consultar-datos').html('Consultar datos');
          $('#btnConsultarDatos, select').removeClass('disabled');
          if (result.ok) {
            graficarInfoConsumo(result);
          } else {
            Swal.fire('Error', result.observacion, 'error');
          }
        })
        .catch(error => {
          $('.text-btn-consultar-datos').html('Consultar datos');
          $('#btnConsultarDatos, select').removeClass('disabled');
          Swal.fire("Error en el servidor.", "Error: " + error.message, "error");
        });
    }
  
    function graficarInfoConsumo(result) {
      $('.consumo-actual-ambiente').html(
        result.datos.consumoAmbiente.kilovatio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      );
      $('.consumo-actual-edificio').html(
        result.datos.consumoEdificio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      );
  
      const resultConsumoActualAmbiente = result.datos.datos.map(e => ({ x: e.fecha, y: parseFloat(e.kilovatio) }));
      const resultConsumoActualEdificio = result.datos.datos.map(e => ({ x: e.fecha, y: parseFloat(e.totalKilovatioEdificio) }));
      const options = {
        series: [{
          name: 'Consumo actual del ambiente',
          data: resultConsumoActualAmbiente
        }, {
          name: 'Consumo actual del edificio',
          data: resultConsumoActualEdificio
        }]
      };
      chart1.updateOptions(options);
      predecirConsumo(result.datos.datos);
    }
  
    function predecirConsumo(datos) {
      fetch('/api/prediccion_datos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
      })
        .then(response => response.json())
        .then(result => {
          if (result.ok) {
            const resultConsumoFuturoAmbiente = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_predicho.toFixed(2)) }));
            const resultConsumoFuturoEdificio = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_total.toFixed(2)) }));
            const consumoFuturoAmbiente = resultConsumoFuturoAmbiente.reduce((acc, item) => acc + item.y, 0);
            const consumoFuturoEdificio = resultConsumoFuturoEdificio.reduce((acc, item) => acc + item.y, 0);
            $('.consumo-futuro-ambiente').html(consumoFuturoAmbiente.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
            $('.consumo-futuro-edificio').html(consumoFuturoEdificio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
            const options = {
              series: [{
                name: 'Consumo futuro del ambiente',
                data: resultConsumoFuturoAmbiente
              }, {
                name: 'Consumo futuro del edificio',
                data: resultConsumoFuturoEdificio
              }]
            };
            chart2.updateOptions(options);
          } else {
            Swal.fire('Ocurrió un error al consultar la información.', '', 'error');
          }
        });
    }
  
    // ============================== Funciones de Voz (Reconocimiento y Síntesis) ==============================
    function toggleVoz() {
      if (estadoAsistente) {
        estadoVoz === "activo" ? detenerEscucha() : iniciarEscucha();
      } else {
        inicializarAsistente();
      }
    }
  
    function iniciarEscucha() {
      $('#btnMicInit').hide();
      $('#btnMicStop').hide();
      $('#btnMicUp').show();
      estadoVoz = "activo";
      recognition.start();
    }
  
    function detenerEscucha() {
      $('#btnMicInit').hide();
      $('#btnMicUp').hide();
      $('#btnMicStop').show();
      estadoVoz = "noactivo";
      recognition.stop();
    }
  
    function gestionarErrorVoz() {
      if (synth.speaking || synth.pending) {
        console.log("Cancelando síntesis de voz pendiente.");
        synth.cancel();
      }
    }
  
    async function hablar(texto) {
      gestionarErrorVoz();
      const speechChunks = makeChunksOfText(texto);
      let indice = 0;
      utterance.onstart = function() {
        clearTimeout(intervalo);
      };
      utterance.onend = function() {
        if (indice < speechChunks.length) {
          console.log("Texto parcial reproducido.");
          indice = voz(speechChunks[indice], indice);
        } else {
          gestionarErrorVoz();
          console.log("Finalizó reproducción de voz.");
          estadoAsistente = "listo";
          permiteGraficaClic = (dataConsumoAct && dataConsumoFut) ? true : false;
          iniciarEscucha();
        }
      };
      utterance.onerror = function(event) {
        console.error('Error en síntesis de voz:', event.error);
        clearTimeout(intervalo);
        indice = voz(speechChunks[Math.max(0, indice - 1)], indice);
      };
      // Eventos adicionales para debug
      utterance.onpause = function(vBoundary) { console.log("Pause event:", vBoundary); };
      utterance.onboundary = function(vBoundary) { console.log("Boundary event:", vBoundary); };
      utterance.onresume = function(vResume) { console.log("Resume event:", vResume); };
      utterance.onmark = function(vMark) { console.log("Mark event:", vMark); };
  
      indice = voz(speechChunks[indice], indice);
    }
  
    function voz(texto, indice) {
      intervalo = setTimeout(() => { synth.cancel(); }, TIEMPO_CORTE * 1000);
      utterance.text = texto;
      synth.speak(utterance);
      return indice + 1;
    }
  
    function makeChunksOfText(text) {
      const maxLength = 190;
      const chunks = [];
      while (text.length > 0) {
        if (text.length <= maxLength) {
          chunks.push(text);
          break;
        }
        let chunk = text.substring(0, maxLength + 1);
        const lastPointIndex = chunk.lastIndexOf('.');
        const lastSpaceIndex = chunk.lastIndexOf(' ');
        if (lastPointIndex !== -1) {
          chunks.push(text.substring(0, lastPointIndex));
          text = text.substring(lastPointIndex + 1);
        } else if (lastSpaceIndex !== -1) {
          chunks.push(text.substring(0, lastSpaceIndex));
          text = text.substring(lastSpaceIndex + 1);
        } else {
          chunks.push(text.substring(0, maxLength));
          text = text.substring(maxLength);
        }
      }
      return chunks;
    }
  
    // ============================== Funciones del Asistente Conversacional ==============================
    function inicializarAsistente() {
      if (estadoAsistente) return;
      estadoAsistente = "detenido";
      $('#btnVoz').attr('disabled', 'true');
      fetch('/inicializar', { method: 'GET' })
        .then(response => response.json())
        .then(data => {
          asistenteFinalizo = false;
          if (data.ok) {
            gMensaje = "Preséntate ante el usuario y dale una bienvenida. Pregunta por su nombre y si es estudiante o docente.";
            conversarAsistente();
          }
        });
    }
  
    function conversarAsistente() {
      estadoAsistente = "detenido";
      const formData = new FormData();
      formData.append('mensaje', gMensaje);
      if (estadoVoz === "activo") detenerEscucha();
      fetch('/conversar', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
          if (data.ok) {
            const respuesta = data.datos;
            if (!$('#contenedor-typing').hasClass('ct-appear')) {
              $('#contenedor-typing').addClass('ct-appear');
            }
            gMensaje = "";
            if (respuesta.asis_funciones) {
              ejecutarFuncion(respuesta.asis_funciones, respuesta.id_run);
            } else if (respuesta.respuesta_msg) {
              const rMensaje = limpiarMensaje(respuesta.respuesta_msg);
              console.log(rMensaje);
              hablar(rMensaje);
            }
          }
        });
    }
  
    async function ejecutarFuncion(asisFunciones, idRun) {
      const funciones = {
        'get_usuario': getDatosUsuario,
        'get_ambiente_edificio': getAmbienteEdificio,
        'get_recomendaciones': getRecomendaciones,
        'get_ids_edificio_piso_ambiente': getInfoLugar,
      };
  
      const respuestas = [];
      for (const afuncion of asisFunciones) {
        const func = funciones[afuncion.funcion_name];
        const rcontent = await func(afuncion);
        respuestas.push({ tool_call_id: afuncion.funcion_id, output: rcontent.reason || rcontent });
      }
      enviarFunciones(respuestas, idRun);
    }
  
    function enviarFunciones(respuestaFunciones, idRun) {
      const formData = new FormData();
      formData.append('toolcall_output', JSON.stringify(respuestaFunciones));
      formData.append('id_run', idRun);
      fetch('/enviar-funciones', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
          if (data.ok) {
            const respuesta = data.datos;
            if (!$('#contenedor-typing').hasClass('ct-appear')) {
              $('#contenedor-typing').addClass('ct-appear');
            }
            gMensaje = "";
            if (respuesta.asis_funciones) {
              ejecutarFuncion(respuesta.asis_funciones, respuesta.id_run);
            } else if (respuesta.respuesta_msg) {
              const rMensaje = limpiarMensaje(respuesta.respuesta_msg);
              console.log(rMensaje);
              hablar(rMensaje);
              gMensaje = rMensaje;
            }
          }
        });
    }
  
    async function getInfoLugar(respuesta) {
      const args = respuesta.funcion_args;
      if (args.idEdificio && args.idPiso && args.idAmbiente && args.fechaInicio && args.fechaFin) {
        return await informacionConsumoAsistente(args.idEdificio, args.idPiso, args.idAmbiente, args.fechaInicio, args.fechaFin);
      } else if (args.idEdificio || args.idPiso || args.idAmbiente) {
        return { success: false, reason: "No tienes la información completa para consultar el consumo energético" };
      } else {
        return { success: false, reason: "Necesitas todos los datos para consultar el consumo energético" };
      }
    }
  
    async function getDatosUsuario(respuesta) {
      const args = respuesta.funcion_args;
      if (args.cargo && args.nombres) {
        return { success: true };
      } else if (args.cargo) {
        return "Pídele al usuario que indique su nombre";
      } else if (args.nombres) {
        return "Pregúntale al usuario si es estudiante o docente";
      } else {
        return "Vuelve a preguntar por el nombre y si es estudiante o docente";
      }
    }
  
    async function getAmbienteEdificio(respuesta) {
      const args = respuesta.funcion_args;
      if (args.edificio && args.ambiente) {
        const formData = new FormData();
        formData.append('edificio', args.edificio);
        formData.append('ambiente', args.ambiente);
        try {
          const response = await fetch('/api/validar_parametros', { method: 'POST', body: formData });
          const data = await response.json();
          if (data.res == 1) {
            if (data.ambiente) {
              $('#select_param_click').hide();
              $('#select_param_voz').show();
              $('#combo_edificio_v').val(args.edificio);
              $('#combo_ambientes_v').val(args.ambiente);
              $('#fecha_busqueda_v').val('2024-01-10');
              informacionConsumo({ idEdificio: data.edificio, idAmbiente: data.ambiente, idPiso: '' });
              return "Se mostrará la información del consumo energético y se darán recomendaciones para optimizar.";
            } else {
              return "El ambiente no se encuentra registrado como parte del edificio.";
            }
          } else {
            return "No se encontró el edificio solicitado. Recuerda que puedes pedir mostrar los edificios registrados.";
          }
        } catch (error) {
          console.error("Error en la solicitud:", error);
          return "Ocurrió un error al consultar los datos. Inténtalo de nuevo.";
        }
      } else {
        return "Vuelve a preguntar por el edificio y el ambiente que se desea consultar.";
      }
    }
  
    async function getRecomendaciones(respuesta) {
      const args = respuesta.funcion_args;
      $('.data-recomendaciones').html(`${args.recomendaciones}`);
      $(".data-recomendaciones").get(0).scrollIntoView({ behavior: 'smooth' });
      return { success: false, reason: "Se han proporcionado las recomendaciones al usuario" };
    }
  
    // ============================== Funciones Utilitarias ==============================
    function groupBy(arr, prop) {
      const map = new Map();
      arr.forEach(item => {
        if (!map.has(item[prop])) {
          map.set(item[prop], []);
        }
        map.get(item[prop]).push(item);
      });
      return Array.from(map.values());
    }
  
    function limpiarMensaje(mensaje) {
      return mensaje.replaceAll('*', '').replaceAll('\n', ' ');
    }
  
    // ============================== Configuración de Voz e Interfaz de Usuario ==============================
    function setearVoces() {
      voces = window.speechSynthesis.getVoices();
      if (!localStorage.getItem('voz_asistente')) {
        const vAsistente = voces.find(v => v.name === "Google español");
        if (vAsistente) {
          localStorage.setItem('voz_asistente', vAsistente.voiceURI);
          utterance.voice = vAsistente;
        } else {
          selectorVoces();
        }
      } else {
        utterance.voice = voces.find(v => v.voiceURI === localStorage.getItem('voz_asistente'));
      }
    }
  
    function verificarVoz() {
      $('#guardar_voz').attr('disabled', !$('#select_voz').val());
    }
  
    function selectorVoces() {
      const vES = voces.filter(v => v.lang === 'es-MX' || v.lang === 'es-ES' || v.lang === 'es-US');
      let opcHTML = "<option value='' selected disabled>Seleccione voz...</option>";
      vES.forEach(v => opcHTML += `<option value="${v.voiceURI}">${v.name}</option>`);
      $('#select_voz').html(opcHTML);
      $('#modal_voces').modal('show');
    }
  
    function reproducir() {
      gestionarErrorVoz();
      const vozURI = $('#select_voz').val();
      if (!vozURI) return;
      const selectVoz = voces.find(v => v.voiceURI === vozURI);
      utterance.text = "Hola, soy el asistente de consumo energético";
      utterance.voice = selectVoz;
      synth.speak(utterance);
      $('#play_voz').attr('disabled', 'true');
      utterance.onend = function() { $('#play_voz').removeAttr('disabled'); };
    }
  
    function guardarVocesDefault() {
      const vAsistente = $('#select_voz').val();
      localStorage.setItem('voz_asistente', vAsistente);
      utterance.voice = voces.find(v => v.voiceURI === vAsistente);
      $('#modal_voces').modal('hide');
      Swal.fire('Se ha guardado la voz correctamente.', '', 'success')
        .then(() => { /* Si es necesario agregar algo tras guardar, se hace aquí */ });
    }
  
    function clickAutorizacion(accion) {
      console.log(accion);
      if (accion === 'A') {
        $('#modal_autorizacion').modal('hide');
        localStorage.setItem('autorizacion', 1);
        inicializarDOM();
      } else {
        location.href = "https://www.google.com/";
      }
    }
  })();
  