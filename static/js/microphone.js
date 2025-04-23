import AudioMotionAnalyzer from 'https://cdn.skypack.dev/audiomotion-analyzer?min';

export default () => {
    let microphoneOpen = false;
    const openedMicroIcon = document.getElementById('openedMicroIcon'),
          closedMicroIcon = document.getElementById('closedMicroIcon');
    let mediaRecorder;
    let audioChunks = [];

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

    const openMicrophone = async () => {
        // Open mic
        openedMicroIcon.hidden = false;
        closedMicroIcon.hidden = true;
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        // Connect stream to audio motion
        audioMotionStream = audioMotion.audioCtx.createMediaStreamSource(stream);
        audioMotion.connectInput(audioMotionStream);
        audioMotion.volume = 0;

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = closeMicrophone;
        mediaRecorder.start();
    };

    const closeMicrophone = () => {
        // Toggle Icon
        openedMicroIcon.hidden = true;
        closedMicroIcon.hidden = false;

        // Close stream for audio motion
        audioMotion.disconnectInput(audioMotionStream);
        audioMotionStream = null;

        const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        audioChunks = [];

        const formData = new FormData();
        formData.append('voice', audioBlob, 'voice.webm');
        fetch('http://localhost:3005/conversar', {
            method: 'POST',
            body: formData
        }).then((response) => {
            return response.json();
        }).then((data) => {
            console.log(data);
            // textResult.textContent = data.text;
            // timeUsed.textContent = data.time.total;
            // sttTime.textContent = data.time.stt;
            // ttsTime.textContent = data.time.tts;
            // audioPlayer.src = `data:audio/wav;base64,${data.audio}`;
        }).catch(error => {
            console.error('Hubo un problema con la petición: ', error);
        });
    };

    document.getElementById('microphoneBtn').addEventListener('click', async () => {
        if( ! microphoneOpen ){
            await openMicrophone();
        } else {
            mediaRecorder.stop();
        }
        microphoneOpen = ! microphoneOpen;
    });
};