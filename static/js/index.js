import AudioMotionAnalyzer from 'https://cdn.skypack.dev/audiomotion-analyzer?min';

const Index = (function () {
  
  let dataEdificios = [];
  let fechaInicio, fechaFin;
  let chart1 = null, chart2 = null;
  let intencionConversar = 'ninguna';

  let microphoneAviable = true;
  let microphoneOpen = false;
  const openedMicroIcon = document.getElementById('btnMicUp'),
        closedMicroIcon = document.getElementById('btnMicStop');
  let mediaRecorder;
  let audioChunks = [];
  const assistantAudioPlayer = document.getElementById('assistantAudioPlayer');
  // Declaramos el controlador a nivel de módulo para poder abortar peticiones anteriores
  let currentAbortController = null;

  const iframe = document.querySelector("iframe");

  // Función para mandar datos al iframe
  function enviarAlIframe(audioBase64) {
    iframe.contentWindow.postMessage(
      { action: "base64", data: audioBase64 }, 
      "*"
    );
  }

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
    
    // if (!microphoneAviable) return;
    
    if (!assistantAudioPlayer.paused) {
      assistantAudioPlayer.pause();
      assistantAudioPlayer.currentTime = 0;
    }

    // Si ya hay una petición en curso, la abortamos antes de lanzar la nueva
    if (currentAbortController) {
      currentAbortController.abort();
    }
    
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
    // microphoneOpen = true;
  };

  const closeMicrophone = async () => {
    // microphoneAviable = false;

    openedMicroIcon.hidden = true;
    closedMicroIcon.hidden = false;

    // Desconectar visualizador
    audioMotion.disconnectInput(audioMotionStream);
    audioMotionStream = null;
    
    // Preparar el blob y enviarlo
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    audioChunks = [];

    // --- VALIDACIÓN: si el blob es muy pequeño, asumimos que no hay voz ---
    const MIN_AUDIO_SIZE = 25000; // bytes (ajusta según pruebas)
    
    if (audioBlob.size < MIN_AUDIO_SIZE) {
      console.log('No se detectó voz (blob demasiado pequeño), no se envía petición.');
      microphoneOpen = false;
      microphoneAviable = true;  // reactivar el micrófono para la siguiente vez
      return;
    }
    
    await Conversar(audioBlob);

    microphoneOpen = false;
  };

  document.getElementById('btnMicrofono').addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
    } else {
      openMicrophone();
    }
    // if (!microphoneOpen) {
    // } else {
    // }
  });

  assistantAudioPlayer.addEventListener('ended', () => {
    console.log("Audio finalizado");
    // microphoneAviable = true;
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
      const idEdificio = $('#combo_edificio option:selected').val();
      const idPiso = $('#combo_pisos option:selected').val();
      const idAmbiente = $('#combo_ambientes option:selected').val();
      console.log(idEdificio, idPiso, idAmbiente);
      if (idEdificio && idPiso && idAmbiente) {
        informacionConsumo({ idEdificio, idPiso, idAmbiente });
      } else {
        Swal.fire('Error', 'Seleccione todos los campos.', 'error');
      }
    });
    // $('#select_voz').on('change', verificarVoz);
    // $('#play_voz').on('click', reproducir);
    // $('#guardar_voz').on('click', guardarVocesDefault);
    $('#btnVerChat').on('click', mostrarChat);
    $('#btnCerrarChat').on('click', cerrarChat)
  }

  function informacionConsumo(params) {
    $('.text-btn-consultar-datos').html('Consultando datos... <span class="indicator-progress">Cargando... <span class="spinner-border spinner-border-sm align-middle ms-2"></span></span>');
    $('#btnConsultarDatos, select').addClass('disabled');
    fetch(`/datos?idEdificacion=${params.idEdificio}&idPiso=${params.idPiso}&idAmbiente=${params.idAmbiente}&fechaInicio=${fechaInicio}&fechaFin=${fechaFin}`)
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

  async function mostrarChat() {
    
    document.querySelector('#btnVerChat').classList.add('disabled');
    document.querySelector('.spinner-ver-chat').classList.remove('d-none');
    document.querySelector('.spinner-ver-chat').classList.add('d-flex');

    await fetch('/chats', { method: 'GET' })
    .then(response => response.json())
    .then(result => {
      document.querySelector('#btnVerChat').classList.remove('disabled');
      document.querySelector('.spinner-ver-chat').classList.remove('d-flex');
      document.querySelector('.spinner-ver-chat').classList.add('d-none');
      
      let resultado = '';
      
      if(result){
        
        result.forEach(e => {
        
          if(['assistant','tool'].includes(e.datos.role)){
            resultado += `
            <div class="message incoming">
              <small class="text-muted">${(e.datos.role === 'assistant' ? 'Asistente' : 'Tool')} • ${moment(e.creado).format('DD MMM YYY HH:Mmm')}</small>
              <pre class="mb-0">${e.datos.content}</pre>
              <div class="reactions">
                <button class="btn btn-sm btn-active-light-success ${e.reaccion === 1 ? `btn-light-success` : ``} reaction-btn" data-id="${e.id}" data-reaction="1">
                  <i class="ki-duotone ki-like fs-1">
                    <span class="path1"></span>
                    <span class="path2"></span>
                  </i>
                </button>
                <button class="btn btn-sm btn-active-light-danger  ${e.reaccion === 0 ? `btn-light-danger` : ``} reaction-btn fs-2" data-id="${e.id}" data-reaction="0">
                  <i class="ki-duotone ki-dislike fs-1">
                    <span class="path1"></span>
                    <span class="path2"></span>
                  </i>
                </button>
              </div>
            </div>`
          }else{
            resultado += `
            <div class="message outgoing">
              <small class="text-light">Tú • ${moment(e.creado).format('DD MMM YYY HH:Mmm')}</small>
              <pre class="mb-0">${e.datos.content}</pre>
            </div>
            `
  
          }
  
        });

      }

      document.querySelector('#chat').innerHTML = resultado;
      
      document.querySelector('#controles').style.display = 'none';
      document.querySelector('.card-avatar').style.display = 'none';
      document.querySelector('.card-chat').style.display = 'flex';

      document.querySelector('#chat').scrollTop = document.querySelector('#chat').scrollHeight;
      
      $('.reaction-btn').off('click').on('click', function() {
        const reaccion = $(this).data('reaction');
        const idMensaje = $(this).attr('data-id');
        
        // Aquí puedes manejar la reacción, por ejemplo, enviarla al servidor
        fetch('/reaccionar-msg', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reaccion, idMensaje })
        })
        .then(response => response.json())
        .then(data => {
          
          $(`.reaction-btn[data-id="${idMensaje}"][data-reaction="1"]`).removeClass('btn-light-success');
          $(`.reaction-btn[data-id="${idMensaje}"][data-reaction="0"]`).removeClass('btn-light-danger');
          
          if (reaccion === 1) {
            $(`.reaction-btn[data-id="${idMensaje}"][data-reaction="1"]`).addClass('btn-light-success');
          } else if (reaccion === 0) {
            $(`.reaction-btn[data-id="${idMensaje}"][data-reaction="0"]`).addClass('btn-light-danger');
          }
          
        })
        .catch(error => {
          console.error('Error al guardar la reacción:', error);
        });
      })
      
    }).catch(error => {
      console.error('Error:', error);
      document.querySelector('#btnVerChat').classList.remove('disabled');
      document.querySelector('.spinner-ver-chat').classList.remove('d-flex');
      document.querySelector('.spinner-ver-chat').classList.add('d-none');
    });

  }

  function cerrarChat() {
    document.querySelector('#controles').style.display = 'flex';
    document.querySelector('.card-avatar').style.display = 'flex';
    document.querySelector('.card-chat').style.display = 'none';
  }

  async function Conversar(audioBlob) {
    
    // Creamos un nuevo controller para esta petición
    currentAbortController = new AbortController();
    const { signal } = currentAbortController;

    const formData = new FormData();
    formData.append('voice', audioBlob, 'voice.webm');
    formData.append('intencion', intencionConversar);

    let reader;
    let textoAcumulado = '';
    let buffer = '';
    const decoder = new TextDecoder('utf-8');

    const output = document.getElementById("recomendaciones");
    output.textContent = "";

    try {
      const res = await fetch('/conversar', {
        method: 'POST',
        body: formData,
        signal,
        headers: { 'Accept': 'application/x-ndjson' } // Indicamos que esperamos NDJSON
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      reader = res.body.getReader();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop(); // deja la última línea incompleta en buffer

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          let msg;
          try {
            msg = JSON.parse(trimmed);
          } catch (e) {
            console.warn('Error al procesar la línea NDJSON:', trimmed);
            continue;
          }

          // console.debug(msg)
          // Manejo de mensajes dependiendo del tipo
          switch (msg.type) {
            case 'token':
              // Concatenar el token para mostrar texto en tiempo real
              textoAcumulado += msg.token || '';
              output.textContent = textoAcumulado;
              output.scrollTop = output.scrollHeight;
              // console.log('Texto acumulado:', textoAcumulado);
              break;
            case 'audio':
              // Aquí puedes manejar los datos de audio (por ejemplo, para reproducir)
              // console.log('Audio recibido', msg.data);
              // audioQueue.push(msg.data); // agrega a la cola para reproducción
              enviarAlIframe(msg.data);
              playNext(); // función que maneja la reproducción
              break;
            case 'info':
              // Información adicional enviada por el backend
              if (msg.data) {
                // console.log("Información adicional recibida:", msg.data);
                ejecutarFuncion(msg.data); // Ejecuta alguna función con los datos
              }
              break;
            case 'grafico':
              // Información adicional enviada por el backend
              if (msg.data) {
                // console.log("Datos de gráficos recibidos:");
                // console.log(msg.data)
                // console.log(JSON.parse(msg.data))
                ejecutarFuncion(JSON.parse(msg.data)); // Ejecuta alguna función con los datos
              }
              break;
            case 'intenciones':
              // Información adicional enviada por el backend
              if (msg.data) {
                // console.log("Datos de gráficos recibidos:");
                // console.log(msg.data)
                // console.log(JSON.parse(msg.data))
                let datosIntenciones = JSON.parse(msg.data);
                intencionConversar = datosIntenciones.siguiente;
              }
              break;
            case 'final':
              // Si el stream terminó o hay una respuesta final
              const respuesta = msg.datos || {};
              if (respuesta.info?.length) {
                ejecutarFuncion(respuesta.info);
              }
              if (respuesta.respuesta) {
                hablar(respuesta); // Aquí manejas la respuesta final (TTS, etc.)
              }
              break;
            case 'end':
              console.log('Stream completo');
              break;
            default:
              console.log('Tipo de mensaje no reconocido:', msg);
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Petición abortada.');
      } else {
        console.error('Hubo un error con la petición:', error);
      }
    } finally {
      if (reader) {
        try { reader.releaseLock(); } catch (e) { console.error(e); }
      }
    }
  }



  // AudioContext para decodificar
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

  // Cola de fragmentos Base64
  const audioQueue = [];
  let isPlaying = false;

  // ============================== Funciones de Voz (Reconocimiento y Síntesis) ==============================
  async function iniciarRecorrido() {
    
    // detenerEscucha();
    document.querySelector('#btnIniciarRecorrido').classList.add('disabled');
    document.querySelector('.spinner-iniciar-recorrido').classList.remove('d-none');
    document.querySelector('.spinner-iniciar-recorrido').classList.add('d-flex');
    
    const output = document.getElementById("recomendaciones");
    output.textContent = "";
    
    try {

      const res = await fetch("/inicializar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stream: true })
      });

      // if (!res.ok) throw new Error(res.statusText);
      
      document.querySelector('#btnIniciarRecorrido').classList.remove('disabled');
      document.querySelector('.spinner-iniciar-recorrido').classList.remove('d-flex');
      document.querySelector('.spinner-iniciar-recorrido').classList.add('d-none');
      
      if (!$('#contenedor-typing').hasClass('ct-appear')) {
        $('#contenedor-typing').addClass('ct-appear');
      }

      /*if(respuesta.info && respuesta.info.length > 0){
        console.log("Informacion adicional");
        ejecutarFuncion(respuesta.info)
      }
      
      if (respuesta.respuesta) {
        hablar(respuesta);
      }*/
      
      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.trim()) continue;
          // console.log(JSON.parse(line))
          const msg = JSON.parse(line);

          if (msg.type === "token") {
            output.textContent += msg.token;
            output.scrollTop = output.scrollHeight;
          }
          else if (msg.type === "audio") {
            // En lugar de reproducir al vuelo, lo añadimos a la cola
            // audioQueue.push(msg.data);
            enviarAlIframe(msg.data);
            playNext();
          }
          else if (msg.type === "end") {
            console.log("Stream completo");
          }
        }
      }
      
    } catch (error) {
      console.error('Error:', error);
      document.querySelector('#btnIniciarRecorrido').classList.remove('disabled');
      document.querySelector('.spinner-iniciar-recorrido').classList.remove('d-flex');
      document.querySelector('.spinner-iniciar-recorrido').classList.add('d-none');
    
    }

  }

  // Función para reproducir el siguiente de la cola
  async function playNext() {
    return false;
    if (isPlaying || audioQueue.length === 0) return;
    isPlaying = true;
    const base64 = audioQueue.shift();

    // Decodificar Base64 → ArrayBuffer
    const raw = atob(base64);
    const buf = new Uint8Array(raw.length);
    for (let i = 0; i < raw.length; i++) buf[i] = raw.charCodeAt(i);

    try {
      const audioBuffer = await audioCtx.decodeAudioData(buf.buffer);
      const source = audioCtx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioCtx.destination);
      source.onended = () => {
        isPlaying = false;
        playNext();  // en cuanto termine, lanzamos el siguiente
      };
      source.start();
    } catch (err) {
      console.error("Error al decodificar/reproducir audio:", err);
      isPlaying = false;
      playNext();
    }
  }

  async function hablar(data) {
    
    assistantAudioPlayer.src = `data:audio/wav;base64,${data.audio}`;
    assistantAudioPlayer.play();
    
  }

  function ejecutarFuncion(aFunciones) {
    const funciones = {
      // 'get_usuario': getDatosUsuario,
      'solicita_prediccion': predecirConsumo3,
      'solicita_recomendaciones': getRecomendaciones,
      'solicita_datos_consumo': getInfoLugar,
    };

    for (const afuncion of aFunciones) {
      const func = funciones[afuncion.nombre];
      func(afuncion.valor);
    }
  }

  function getInfoLugar(data) {
    console.debug(data)
    if(data.ok){
      let ops = '';
      let params = data.params;
      const edificio = dataEdificios.find(e => e.nombre == params.idEdificio);
      console.debug(edificio)

      if(edificio){
        const piso = edificio.pisos.find(p => p.nombre == params.idPiso);
        if (piso) {
          ops = "<option value='' selected disabled>Seleccionar</option>";
          edificio.pisos.forEach(p => ops += `<option value='${p.id}'>${p.nombre}</option>`);
          $('#combo_pisos').html(ops);

          const ambiente = piso.ambientes.find(a => a.nombre == params.idAmbiente);
          if (ambiente) {
            ops = "<option value='' selected disabled>Seleccionar</option>";
            groupBy(piso.ambientes, 'tipoAmbiente').forEach(group => {
              ops += `<optgroup label="${group[0].tipoAmbiente}">`;
              group.forEach(item => ops += `<option value="${item.id}">${item.nombre}</option>`);
              ops += `</optgroup>`;
            });
            $('#combo_ambientes').html(ops);
          }
        }
      }

      $('#combo_edificio option').filter(function() { return $(this).text() === params.idEdificio; }).prop('selected', true);
      $('#combo_edificio').trigger('change');
      $('#combo_pisos option').filter(function() { return $(this).text() === params.idPiso; }).prop('selected', true);
      $('#combo_pisos').trigger('change');
      $('#combo_ambientes option').filter(function() { return $(this).text() === params.idAmbiente; }).prop('selected', true);
      $('#combo_ambientes').trigger('change');
      
      initFechas({ start: moment(params.fechaInicio), end: moment(params.fechaFin) });
      //console.log(respuesta);
    }

    graficarInfoConsumo(data);
    
  }
  
  function getRecomendaciones(respuesta) {
    //const args = respuesta;
    $('.data-recomendaciones').html(`${respuesta}`);
    $(".data-recomendaciones").get(0).scrollIntoView({ behavior: 'smooth' });
    //return { success: false, reason: "Se han proporcionado las recomendaciones al usuario" };
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
        result.datos.forEach(element => ops += `<option value='${element.id}'>${element.edificacion}</option>`);
        $('#combo_edificio').html(ops);
        // llenarModalInfoEdificios();
      } else {
        Swal.fire('Error', result.observacion, 'error');
      }
    } catch (error) {
      Swal.fire("Error en el servidor.", "Error: " + error.message, "error");
    }
  }

  function graficarInfoConsumo(result) {
    console.log(result);
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
    if(result.datos.datos.length > 0){
      //predecirConsumo(result.datos.datos);
    }
  }

  function predecirConsumo3(datos) {
    const resultConsumoFuturoAmbiente = datos.map(e => ({ x: e.fecha, y: Number(e.consumo_predicho.toFixed(2)) }));
    //const resultConsumoFuturoEdificio = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_total.toFixed(2)) }));
    const resultConsumoFuturoEdificio = datos.map(e => ({ x: e.fecha, y: Number(e.consumo_predicho.toFixed(2)) }));
    const consumoFuturoAmbiente = resultConsumoFuturoAmbiente.reduce((acc, item) => acc + item.y, 0);
    //const consumoFuturoEdificio = resultConsumoFuturoEdificio.reduce((acc, item) => acc + item.y, 0);
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
  }

  function predecirConsumo() {
    const idEdificio = $('#combo_edificio option:selected').val();
    const idPiso = $('#combo_pisos option:selected').val();
    const idAmbiente = $('#combo_ambientes option:selected').val();
    const fecha = new Date().toISOString().split('T')[0]

    fetch(`/api/prediccion?edificio=${idEdificio}&piso=${idPiso}&ambiente=${idAmbiente}&fecha=${fecha}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(result => {
      if (result.ok) {
        const resultConsumoFuturoAmbiente = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_predicho.toFixed(2)) }));
        //const resultConsumoFuturoEdificio = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_total.toFixed(2)) }));
        const resultConsumoFuturoEdificio = result.datos.map(e => ({ x: e.fecha, y: Number(e.consumo_predicho.toFixed(2)) }));
        const consumoFuturoAmbiente = resultConsumoFuturoAmbiente.reduce((acc, item) => acc + item.y, 0);
        //const consumoFuturoEdificio = resultConsumoFuturoEdificio.reduce((acc, item) => acc + item.y, 0);
        const consumoFuturoEdificio = resultConsumoFuturoEdificio.reduce((acc, item) => acc + item.y, 0);
        $('.consumo-futuro-ambiente').html(consumoFuturoAmbiente.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        $('.consumo-futuro-edificio').html(consumoFuturoEdificio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
        //$('.consumo-futuro-edificio').html(consumoFuturoEdificio.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
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
    return mensaje.replaceAll('*', '').replaceAll('\n', '. ');
  }

})();