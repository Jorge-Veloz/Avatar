import AudioMotionAnalyzer from 'https://cdn.skypack.dev/audiomotion-analyzer?min';

const Index = (function () {
  
  let dataEdificios = [];
  let fechaInicio, fechaFin;
  let chart1 = null, chart2 = null;

  let microphoneAviable = true;
  let microphoneOpen = false;
  const openedMicroIcon = document.getElementById('btnMicUp'),
        closedMicroIcon = document.getElementById('btnMicStop');
  let mediaRecorder;
  let audioChunks = [];
  const assistantAudioPlayer = document.getElementById('assistantAudioPlayer');

  const audioMotion = new AudioMotionAnalyzer(document.getElementById('audioMotionAnalyzer'), {
    height: 70,
    ansiBands: false,
    showScaleX: false,
    bgAlpha: 0,
    overlay: true,
    mode: 2,
    frequencyScale: "log",
    showPeaks: false,
    reflexRatio: 0.5,
    reflexAlpha: 1,
    reflexBright: 1,
    smoothing: 0.7
  });
  let audioMotionStream;

  // Parámetros de detección de silencio
  const silenceThreshold = 0.02;      // RMS mínimo para considerar "habla"
  const silenceDelay = 1000;          // ms que debe durar el silencio
  let silenceStart = null;
  let silenceInterval;

  // ============================== Inicialización General ==============================
  $(document).ready(async function() {
    initMicrofono();
    initConsentimiento();
    initFechas();
    initGraficos();
    await bindUIEvents();
    await getEdificios();
  });

  const openMicrophone = async () => {
    
    if (!microphoneAviable) return;

    // Mostrar icono de grabando
    openedMicroIcon.hidden = false;
    closedMicroIcon.hidden = true;

    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    // Conectar al visualizador
    audioMotionStream = audioMotion.audioCtx.createMediaStreamSource(stream);
    audioMotion.connectInput(audioMotionStream);
    audioMotion.volume = 0;

    // Crear analysers para detectar silencio
    const analyser = audioMotion.audioCtx.createAnalyser();
    analyser.fftSize = 2048;
    audioMotionStream.connect(analyser);
    const dataArray = new Uint8Array(analyser.fftSize);
    silenceStart = null;

    // Cada 200 ms comprobamos el nivel de RMS
    silenceInterval = setInterval(() => {
      analyser.getByteTimeDomainData(dataArray);
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const norm = (dataArray[i] - 128) / 128;
        sum += norm * norm;
      }
      const rms = Math.sqrt(sum / dataArray.length);

      if (rms > silenceThreshold) {
        // Volumen detectado: resetamos el contador de silencio
        silenceStart = null;
      } else {
        // No hay volumen: empezamos o comprobamos el tiempo de silencio
        if (!silenceStart) {
          silenceStart = Date.now();
        } else if (Date.now() - silenceStart > silenceDelay) {
          // Silencio prolongado: detenemos la grabación
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
          }
          clearInterval(silenceInterval);
        }
      }
    }, 200);

    mediaRecorder.ondataavailable = event => {
      audioChunks.push(event.data);
    };

    mediaRecorder.onstop = () => {
      clearInterval(silenceInterval);
      closeMicrophone();
    };

    mediaRecorder.start();
    microphoneOpen = true;
  };

  const closeMicrophone = () => {
    microphoneAviable = false;
    openedMicroIcon.hidden = true;
    closedMicroIcon.hidden = false;

    // Desconectar visualizador
    audioMotion.disconnectInput(audioMotionStream);
    audioMotionStream = null;

    // Preparar el blob y enviarlo
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    audioChunks = [];
    const formData = new FormData();
    formData.append('voice', audioBlob, 'voice.webm');

    fetch('/conversar', {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      // Reproducir la respuesta de audio
      console.log(data.datos)
      assistantAudioPlayer.src = `data:audio/wav;base64,${data.datos.audio}`;
      if (microphoneOpen) return;
      assistantAudioPlayer.play();
      
      // TODO: mostrar data.text si quieres el texto
    })
    .catch(error => {
      microphoneAviable = true;
      console.error('Hubo un problema con la petición:', error);
    });

    microphoneOpen = false;
  };

  document.getElementById('btnMicrofono').addEventListener('click', () => {
    if (!microphoneOpen) {
      openMicrophone();
    } else {
      mediaRecorder.stop();
    }
  });

  assistantAudioPlayer.addEventListener('ended', () => {
    console.log("Audio finalizado");
    microphoneAviable = true;
    openMicrophone();
    // document.querySelector('#btnIniciarRecorrido').classList.remove('disabled');
  });

  // document.getElementById('infoBtn').addEventListener('click', () => {
  //   if (microphoneOpen) return;
  //   assistantAudioPlayer.play();
  // });

  async function bindUIEvents() {
    $('#btnIniciarRecorrido').on('click', await iniciarRecorrido);
    $('#combo_edificio').on('change', onEdificioChange);
    $('#combo_pisos').on('change', onPisoChange);
    $('#btnConsultarDatos').on('click', function() {
      const idEdificio = $('#combo_edificio option:selected').text();
      const idPiso = $('#combo_pisos option:selected').text();
      const idAmbiente = $('#combo_ambientes option:selected').text();
      if (idEdificio && idPiso && idAmbiente) {
        informacionConsumo({ idEdificio, idPiso, idAmbiente });
      } else {
        Swal.fire('Error', 'Seleccione todos los campos.', 'error');
      }
    });
    // $('#select_voz').on('change', verificarVoz);
    // $('#play_voz').on('click', reproducir);
    // $('#guardar_voz').on('click', guardarVocesDefault);
    // $('#mostrarChat').on('click', mostrarChat);
  }

  // ============================== Funciones de Voz (Reconocimiento y Síntesis) ==============================
  async function iniciarRecorrido() {
    
    // detenerEscucha();
    
    document.querySelector('#btnIniciarRecorrido').classList.add('disabled');
    document.querySelector('.spinner-iniciar-recorrido').classList.remove('d-none');
    document.querySelector('.spinner-iniciar-recorrido').classList.add('d-flex');

    await fetch('/inicializar', { method: 'GET' })
      .then(response => response.json())
      .then(result => {

        document.querySelector('#btnIniciarRecorrido').classList.remove('disabled');
        document.querySelector('.spinner-iniciar-recorrido').classList.remove('d-flex');
        document.querySelector('.spinner-iniciar-recorrido').classList.add('d-none');

        // asistenteFinalizo = false;
        if (result.ok) {
          
          const respuesta = result.datos;
          
          if (!$('#contenedor-typing').hasClass('ct-appear')) {
            $('#contenedor-typing').addClass('ct-appear');
          }
          
          if(respuesta.info && respuesta.info.length > 0){
            console.log("Informacion adicional");
            ejecutarFuncion(respuesta.info)
          }
          
          if (respuesta.respuesta) {
            hablar(respuesta);
          }
        }
      }).catch(error => {
        console.error('Error:', error);
        document.querySelector('#btnIniciarRecorrido').classList.remove('disabled');
        document.querySelector('.spinner-iniciar-recorrido').classList.remove('d-flex');
        document.querySelector('.spinner-iniciar-recorrido').classList.add('d-none');
      });
  }

  async function hablar(data) {
    console.log("Texto a hablar: " + data.respuesta);
    assistantAudioPlayer.src = `data:audio/wav;base64,${data.audio}`;
    assistantAudioPlayer.play();
    
  }
  
  // ============================== Funciones para Llamadas a la API y Gestión de Datos ==============================
  async function getEdificios() {
    $('#combo_edificio, #combo_pisos, #combo_ambientes').html("<option value='0' selected disabled>Cargando...</option>");
    try {
      const response = await fetch(`/edificios`);
      const result = await response.json();
      $('#combo_edificio, #combo_pisos, #combo_ambientes').html("<option value='0' selected disabled>Seleccionar</option>");
      if (result.ok) {
        dataEdificios = result.datos;
        let ops = "<option value='' selected disabled>Seleccione el edificio</option>";
        result.datos.forEach(element => ops += `<option value='${element.id}'>${element.nombre}</option>`);
        $('#combo_edificio').html(ops);
        // llenarModalInfoEdificios();
      } else {
        Swal.fire('Error', result.observacion, 'error');
      }
    } catch (error) {
      Swal.fire("Error en el servidor.", "Error: " + error.message, "error");
    }
  }

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
      // inicializarDOM();
    } else {
      $('#modal_autorizacion').modal('show');
    }
    $('#rechazar_auto').on('click', () => clickAutorizacion('R'));
    $('#aceptar_autor').on('click', () => clickAutorizacion('A'));
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

  function initFechas(params = {}) {
    const start = params.start ? params.start : moment();
    const end = params.end ? params.end : moment();
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

  function clickAutorizacion(accion) {
    console.log(accion);
    if (accion === 'A') {
      $('#modal_autorizacion').modal('hide');
      localStorage.setItem('autorizacion', 1);
      // inicializarDOM();
    } else {
      location.href = "https://www.google.com/";
    }
  }

})();