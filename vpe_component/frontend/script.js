// Global variables
let pc = null;
let stream = null;
let transcript = [];
let sessionToken = null;

// Receive props from Streamlit
window.streamlitReceiveProps = function (props) {
    sessionToken = props.args.ephemeralToken;
};

document.addEventListener("DOMContentLoaded", () => {
    const startBtn = document.getElementById("startBtn");
    const stopBtn = document.getElementById("stopBtn");
    const statusBox = document.getElementById("statusBox");

    startBtn.onclick = async () => {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        statusBox.innerHTML = "Initializing conversation...";

        transcript = [];

        try {
            await startConversation();
            statusBox.innerHTML = "🎤 Conversation started. Speak freely!";
        } catch (e) {
            statusBox.innerHTML = "❌ Error starting connection: " + e;
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    };

    stopBtn.onclick = () => {
        stopBtn.disabled = true;
        startBtn.disabled = false;

        statusBox.innerHTML = "Conversation ended. Sending transcript...";

        if (pc) pc.close();
        if (stream) {
            stream.getTracks().forEach((t) => t.stop());
        }

        // Send transcript back to Streamlit
        Streamlit.setComponentValue(transcript);

        statusBox.innerHTML = "Transcript sent!";
    };
});

// ---------------------------
// OpenAI Realtime WebRTC
// ---------------------------

async function startConversation() {
    if (!sessionToken) throw new Error("No ephemeral token received");

    // WebRTC peer connection
    pc = new RTCPeerConnection();

    // Create data channel
    const dc = pc.createDataChannel("oai-events");
    dc.onmessage = (event) => handleMessage(JSON.parse(event.data));

    // Add microphone stream
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((t) => pc.addTrack(t, stream));

    // Create offer
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    // Send offer to OpenAI
    const base64SDP = btoa(JSON.stringify(pc.localDescription));
    const response = await fetch(
        `https://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17`,
        {
            method: "POST",
            headers: {
                Authorization: `Bearer ${sessionToken}`,
                "OpenAI-Beta": "realtime=v1",
                "Content-Type": "application/sdp",
            },
            body: base64SDP,
        }
    );

    const answerSDP = await response.text();
    const remoteDesc = new RTCSessionDescription(
        JSON.parse(atob(answerSDP))
    );

    await pc.setRemoteDescription(remoteDesc);
}

// ---------------------------
// Handle incoming messages
// ---------------------------

function handleMessage(msg) {
    if (msg.type === "response.output_text.delta") {
        const text = msg.delta;

        // Append last message or create new one
        if (
            transcript.length > 0 &&
            transcript[transcript.length - 1].role === "assistant"
        ) {
            transcript[transcript.length - 1].content += text;
        } else {
            transcript.push({ role: "assistant", content: text });
        }
    }

    if (msg.type === "input_audio_transcription.completed") {
        transcript.push({
            role: "user",
            content: msg.transcript,
        });
    }
}
