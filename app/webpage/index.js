let mediaRecorder;
let audioChunks = [];
let currentSession_id = null;
let recordingInterval = null;
let activeStream = null;


async function startRecordingSession(alias){
    currentSession_id = crypto.randomUUID();
    audioChunks = []

    await fetch('http://localhost:8000/api/v1/scribe/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json'},
        body: JSON.stringify({ session_id: currentSession_id, patient_alias: alias})
    });
    activeStream = await navigator.mediaDevices.getUserMedia({ audio:true });
    mediaRecorder = new MediaRecorder(activeStream, { mimeType: 'audio/webm' });

    mediaRecorder.ondataavailable = async(event) => {
        if (event.data.size > 0) {
            audioChunks.push(event.data);
        } 
    }

    mediaRecorder.onstop = async () => {
        const completeBlob = new Blob(audioChunks, {type: 'audio/webm'});

        const formData = new FormData();
        formData.append("session_id",currentSession_id);
        formData.append("audio_chunk", completeBlob, "recording.webm");
        console.log(formData);
        await fetch('http://localhost:8000/api/v1/scribe/audio-chunk', {
                method: 'POST',
                body: formData
            });
    }
    showView("recording_session","patient_alias")
    mediaRecorder.start();
    console.log("Recording started");
}


document.addEventListener('DOMContentLoaded', () => {
    // fetchSessions();

    const form = document.getElementById('new_patient');
    console.log(form);
    form.addEventListener('submit', async(event) => {
        event.preventDefault();
        console.log(document.getElementById('patient_id'));
        const input = document.getElementById('patient_id');
        const alias = input.value.trim();

        if (!alias) return;

        await startRecordingSession(alias);
        input.value = '';
    });

    const stopBtn = document.getElementById('stop');
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }

            if (activeStream) {
                activeStream.getTracks().forEach(track => track.stop());
            }
            showView('patient_alias', 'recording_session');
            alert("Session recording stopped and saved to volatile memory!");
        });
    }
    const tbody = document.querySelector('sessions tbody');
    tbody.addEventListener('click', (e) => {
        if (e.target.classList.contains('finalize-btn')) {
            const sessionId = e.target.getAttribute('data-id');
            summarize(sessionId);
        }
    })
});


async function fetchSessions(){
    try {
        const response = await fetch('http://localhost:8000/api/v1/scribe/sessions');

        if (!response.ok){
            throw new Error(`Http error! Status: ${response.status}`);
        }

        const records = await response.json();

        const tbody = document.querySelector('sessions tbody');
        tbody.innerHTML = '';

        records.forEach(record => {
            const tr = document.createElement('tr');

            tr.innerHTML = `
                <td>${record.session_id}</td>
                <td>${record.patient_alias}</td>
                <td><button class="finalize-btn" data-id="${record.session_id}">Summarize</button></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Failed to load table data:', error);
    }
}



async function summarize(sessionId) {
    try {
        const response = await fetch(`http://localhost:8000/api/v1/scribe/finalize/${sessionId}`, {
            method:'POST'
        });
        if (!response.ok) throw new Error("Failed to finalize sesson");

        const data = await response.json();

        const noteWindow = window.open("","_blank");
        noteWindow.document.write(`
            <html>
                <head>
                    <title>Clinical SOAP Note</title>
                    <style>
                        body { font-family: sans-serif; padding: 40px; line-height: 1.6; max-width: 800px; margin: auto; }
                        pre { white-space: pre-wrap; background: #f4f4f4; padding: 20px; border-radius: 8px; }
                    </style>
                </head>
                <body>
                    <h2>Finalized Clinical Note</h2>
                    <pre>${data.soap_note}</pre>
                </body>
            </html>`);

        fetchSessions();
    } catch (error) {
        console.error("Error finalizing session:",error);
    }    
}

function showView(viewIdOn,viewIdOff) {
    document.getElementById(viewIdOff).style.display = 'none';
    document.getElementById(viewIdOn).style.display = 'block';
}