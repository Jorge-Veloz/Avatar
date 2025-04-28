import AudioMotionAnalyzer from 'https://cdn.skypack.dev/audiomotion-analyzer?min';

export default () => {
    let microphoneAviable = true;
    let microphoneOpen = false;
    const openedMicroIcon = document.getElementById('openedMicroIcon'),
          closedMicroIcon = document.getElementById('closedMicroIcon');
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

        fetch('http://localhost:3005/assistant/talk', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            // Reproducir la respuesta de audio
            assistantAudioPlayer.src = `data:audio/wav;base64,${data.audio}`;
            // TODO: mostrar data.text si quieres el texto
        })
        .catch(error => {
            microphoneAviable = true;
            console.error('Hubo un problema con la petición:', error);
        });

        microphoneOpen = false;
    };

    document.getElementById('microphoneBtn').addEventListener('click', () => {
        if (!microphoneOpen) {
            openMicrophone();
        } else {
            mediaRecorder.stop();
        }
    });

    assistantAudioPlayer.addEventListener('ended', () => {
        microphoneAviable = true;
    });

    document.getElementById('infoBtn').addEventListener('click', () => {
        if (microphoneOpen) return;
        assistantAudioPlayer.play();
    });
};
