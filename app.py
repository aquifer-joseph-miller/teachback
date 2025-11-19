# app.py - Simple manual paste approach

import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import time
import json

# Configuration
FEEDBACK_ASSISTANTS = {
    "Mrs. Miller Feedback": "asst_J2yNXKyAVxZ9yhxVD1o4roNh",
}

MRS_MILLER_PROMPT_ID = "pmpt_691cc606dfb4819491acd1328e0488dd0854e783a6e7f3ec"
PROMPT_VERSION = "4"

class VPERealtimeApp:
    def __init__(self):
        self.setup_openai()
        self.init_session_state()
    
    def setup_openai(self):
        """Initialize OpenAI client."""
        try:
            self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            self.api_key = st.secrets["OPENAI_API_KEY"]
        except KeyError:
            st.error("OpenAI API key not found.")
            st.stop()
    
    def init_session_state(self):
        """Initialize session state."""
        if "conversation_active" not in st.session_state:
            st.session_state.conversation_active = True
    
    def create_realtime_session(self):
        """Create ephemeral token with input transcription."""
        try:
            import requests
            
            response = requests.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "OpenAI-Beta": "realtime=v1"
                },
                json={
                    "prompt": {
                        "id": MRS_MILLER_PROMPT_ID,
                        "version": PROMPT_VERSION
                    },
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("client_secret", {}).get("value")
            else:
                st.error(f"Session failed: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error: {e}")
            return None
    
    def realtime_component(self, ephemeral_token):
        """Create the Realtime API component."""
        
        component_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    max-width: 900px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    padding: 30px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                }}
                .status {{
                    text-align: center;
                    font-size: 24px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    padding: 20px;
                    border-radius: 10px;
                    background: #f0f0f0;
                }}
                .status.connected {{
                    background: #4CAF50;
                    color: white;
                    animation: pulse 2s infinite;
                }}
                .controls {{
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    margin-bottom: 20px;
                }}
                button {{
                    padding: 15px 40px;
                    font-size: 18px;
                    border: none;
                    border-radius: 50px;
                    cursor: pointer;
                    font-weight: bold;
                    transition: all 0.3s;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                }}
                button:hover:not(:disabled) {{
                    transform: translateY(-2px);
                }}
                #connectBtn {{
                    background: #4CAF50;
                    color: white;
                }}
                #disconnectBtn {{
                    background: #f44336;
                    color: white;
                }}
                button:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                    transform: none;
                }}
                .transcript {{
                    background: #f9f9f9;
                    border-radius: 10px;
                    padding: 20px;
                    max-height: 400px;
                    overflow-y: auto;
                }}
                .message {{
                    margin: 15px 0;
                    padding: 15px;
                    border-radius: 10px;
                }}
                .user {{
                    background: #e3f2fd;
                    margin-left: 40px;
                    border-left: 4px solid #2196F3;
                }}
                .assistant {{
                    background: #f3e5f5;
                    margin-right: 40px;
                    border-left: 4px solid #9C27B0;
                }}
                .speaker {{
                    font-weight: bold;
                    margin-bottom: 5px;
                }}
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.7; }}
                }}
                .debug {{
                    background: #e8f5e9;
                    padding: 6px;
                    margin: 2px 0;
                    font-size: 10px;
                    font-family: monospace;
                    border-radius: 3px;
                }}
                #debugLog {{
                    max-height: 100px;
                    overflow-y: auto;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 8px;
                    margin: 10px 0;
                }}
                #copyInstructions {{
                    display: none;
                    background: #fff3cd;
                    border: 2px solid #ffc107;
                    border-radius: 10px;
                    padding: 20px;
                    margin-top: 20px;
                }}
                #copyInstructions.show {{
                    display: block;
                }}
                .copy-btn {{
                    background: #2196F3;
                    color: white;
                    padding: 10px 20px;
                    margin-top: 10px;
                }}
                #transcriptOutput {{
                    background: white;
                    border: 1px solid #ddd;
                    padding: 10px;
                    margin: 10px 0;
                    font-family: monospace;
                    font-size: 12px;
                    max-height: 200px;
                    overflow-y: auto;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="text-align: center; margin-bottom: 20px;">
                    🎤 Voice Conversation with Mrs. Miller
                </h2>
                
                <div id="status" class="status">Ready to connect</div>
                
                <div class="controls">
                    <button id="connectBtn" onclick="connectRealtime()">
                        🎤 Start Conversation
                    </button>
                    <button id="disconnectBtn" onclick="endConversation()" disabled>
                        ⏹️ End Conversation
                    </button>
                </div>
                
                <div id="debugLog"></div>
                
                <div class="transcript" id="transcript">
                    <p style="text-align: center; color: #999;">
                        Conversation will appear here...
                    </p>
                </div>
                
                <div id="copyInstructions">
                    <h3>📋 Transcript Ready!</h3>
                    <p><strong>Copy the text below and paste it in the box at the bottom of the page:</strong></p>
                    <div id="transcriptOutput"></div>
                    <button class="copy-btn" onclick="copyTranscript()">📋 Copy to Clipboard</button>
                </div>
            </div>

            <script>
                let peerConnection = null;
                let dataChannel = null;
                let audioStream = null;
                const ephemeralToken = "{ephemeral_token}";
                let conversationTranscript = [];
                
                function debugLog(msg) {{
                    console.log(msg);
                    const log = document.getElementById('debugLog');
                    const entry = document.createElement('div');
                    entry.className = 'debug';
                    entry.textContent = new Date().toLocaleTimeString() + ': ' + msg;
                    log.appendChild(entry);
                    log.scrollTop = log.scrollHeight;
                }}
                
                async function connectRealtime() {{
                    try {{
                        document.getElementById('connectBtn').disabled = true;
                        debugLog('🎤 Requesting microphone...');
                        
                        audioStream = await navigator.mediaDevices.getUserMedia({{ 
                            audio: {{ echoCancellation: true, noiseSuppression: true }}
                        }});
                        
                        debugLog('✅ Mic granted');
                        
                        peerConnection = new RTCPeerConnection();
                        audioStream.getTracks().forEach(track => {{
                            peerConnection.addTrack(track, audioStream);
                        }});
                        
                        peerConnection.ontrack = (event) => {{
                            const audio = new Audio();
                            audio.srcObject = event.streams[0];
                            audio.play();
                        }};
                        
                        dataChannel = peerConnection.createDataChannel('oai-events');
                        dataChannel.onopen = () => debugLog('📡 Data channel open');
                        dataChannel.onmessage = (event) => handleEvent(event.data);
                        
                        peerConnection.onconnectionstatechange = () => {{
                            if (peerConnection.connectionState === 'connected') {{
                                document.getElementById('status').textContent = '🎤 Connected - Speak now';
                                document.getElementById('status').className = 'status connected';
                                document.getElementById('disconnectBtn').disabled = false;
                                debugLog('🟢 CONNECTED');
                            }}
                        }};
                        
                        const offer = await peerConnection.createOffer();
                        await peerConnection.setLocalDescription(offer);
                        
                        const response = await fetch('https://api.openai.com/v1/realtime', {{
                            method: 'POST',
                            headers: {{
                                'Authorization': `Bearer ${{ephemeralToken}}`,
                                'Content-Type': 'application/sdp'
                            }},
                            body: offer.sdp
                        }});
                        
                        const answerSdp = await response.text();
                        await peerConnection.setRemoteDescription({{ type: 'answer', sdp: answerSdp }});
                        
                    }} catch (error) {{
                        debugLog('❌ Error: ' + error.message);
                        document.getElementById('connectBtn').disabled = false;
                    }}
                }}
                
                function handleEvent(data) {{
                    try {{
                        const event = JSON.parse(data);
                        
                        if (event.type === 'conversation.item.input_audio_transcription.completed') {{
                            const text = event.transcript;
                            if (text) {{
                                debugLog('🎓 STUDENT: ' + text.substring(0, 30));
                                addMessage('user', text);
                                conversationTranscript.push({{ role: 'user', content: text }});
                            }}
                        }}
                        
                        if (event.type === 'response.audio_transcript.done') {{
                            const text = event.transcript;
                            if (text) {{
                                debugLog('👩‍⚕️ MILLER: ' + text.substring(0, 30));
                                addMessage('assistant', text);
                                conversationTranscript.push({{ role: 'assistant', content: text }});
                            }}
                        }}
                        
                    }} catch (error) {{
                        console.error('Event error:', error);
                    }}
                }}
                
                function addMessage(role, content) {{
                    const transcript = document.getElementById('transcript');
                    if (transcript.children.length === 1 && transcript.children[0].tagName === 'P') {{
                        transcript.innerHTML = '';
                    }}
                    
                    const msg = document.createElement('div');
                    msg.className = `message ${{role}}`;
                    
                    const speaker = document.createElement('div');
                    speaker.className = 'speaker';
                    speaker.textContent = role === 'user' ? '🎓 Student' : '👩‍⚕️ Mrs. Miller';
                    
                    const text = document.createElement('div');
                    text.textContent = content;
                    
                    msg.appendChild(speaker);
                    msg.appendChild(text);
                    transcript.appendChild(msg);
                    transcript.scrollTop = transcript.scrollHeight;
                }}
                
                function endConversation() {{
                    debugLog('💾 Ending... ' + conversationTranscript.length + ' messages');
                    
                    if (audioStream) audioStream.getTracks().forEach(t => t.stop());
                    if (dataChannel) dataChannel.close();
                    if (peerConnection) peerConnection.close();
                    
                    document.getElementById('status').textContent = 'Conversation Ended';
                    document.getElementById('status').className = 'status';
                    document.getElementById('disconnectBtn').disabled = true;
                    
                    // Show copy instructions
                    const instructions = document.getElementById('copyInstructions');
                    instructions.className = 'show';
                    
                    // Display transcript
                    const output = document.getElementById('transcriptOutput');
                    output.textContent = JSON.stringify(conversationTranscript, null, 2);
                    
                    debugLog('✅ Transcript ready to copy!');
                    debugLog('📊 Total messages: ' + conversationTranscript.length);
                    
                    // Scroll to instructions
                    instructions.scrollIntoView({{ behavior: 'smooth' }});
                }}
                
                function copyTranscript() {{
                    const output = document.getElementById('transcriptOutput');
                    const text = output.textContent;
                    
                    navigator.clipboard.writeText(text).then(() => {{
                        alert('✅ Transcript copied! Scroll down and paste it in the box below.');
                    }}).catch(err => {{
                        alert('Please manually select and copy the text above.');
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        return component_html
    
    def generate_feedback(self, transcript_data):
        """Generate feedback from transcript."""
        transcript_text = "\n\n".join([
            f"{'STUDENT' if msg['role'] == 'user' else 'MRS. MILLER'}: {msg['content']}"
            for msg in transcript_data
        ])
        
        st.markdown("### 📝 Conversation Transcript")
        with st.expander("View Full Transcript"):
            st.text_area("", transcript_text, height=200, key="transcript_display")
        
        try:
            feedback_thread = self.client.beta.threads.create()
            
            self.client.beta.threads.messages.create(
                thread_id=feedback_thread.id,
                role="user",
                content=f"""You are an expert clinical skills rater. Use the five-domain assessment framework.

Transcript:

{transcript_text}

Provide comprehensive feedback."""
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=feedback_thread.id,
                assistant_id=FEEDBACK_ASSISTANTS["Mrs. Miller Feedback"]
            )
            
            with st.spinner("🧠 Generating comprehensive feedback..."):
                while True:
                    status = self.client.beta.threads.runs.retrieve(
                        thread_id=feedback_thread.id,
                        run_id=run.id
                    )
                    
                    if status.status == "completed":
                        break
                    elif status.status in ["failed", "cancelled", "expired"]:
                        st.error(f"Failed: {status.status}")
                        return
                    
                    time.sleep(2)
                
                messages = self.client.beta.threads.messages.list(
                    thread_id=feedback_thread.id,
                    limit=1
                )
                
                if messages.data:
                    feedback = messages.data[0].content[0].text.value
                    
                    st.markdown("---")
                    st.subheader("📋 Comprehensive Feedback")
                    st.markdown(feedback)
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Download Transcript",
                            transcript_text,
                            file_name="transcript.txt",
                            use_container_width=True
                        )
                    with col2:
                        st.download_button(
                            "📥 Download Feedback",
                            feedback,
                            file_name="feedback.txt",
                            use_container_width=True
                        )
        
        except Exception as e:
            st.error(f"Error: {e}")
    
    def run(self):
        """Main application."""
        st.set_page_config(
            page_title="VPE - Mrs. Miller",
            page_icon="🎤",
            layout="wide"
        )
        
        st.title("🎤 Virtual Patient Encounter - Mrs. Miller")
        st.markdown("*High Value Care Case 04*")
        
        with st.sidebar:
            st.header("Instructions")
            st.info("""
            1. Click "Start Conversation"
            2. Allow microphone access  
            3. Speak with Mrs. Miller
            4. Click "End Conversation"
            5. **Copy the transcript** shown in the yellow box
            6. **Paste it below** and click "Generate Feedback"
            """)
            
            if st.button("🔄 Start New Session", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
        
        # Show conversation interface
        if st.session_state.conversation_active:
            ephemeral_token = self.create_realtime_session()
            
            if ephemeral_token:
                st.success("✅ Voice session ready!")
                html_code = self.realtime_component(ephemeral_token)
                components.html(html_code, height=850, scrolling=True)
        
        # Feedback generation section
        st.markdown("---")
        st.markdown("## 📋 Generate Feedback")
        st.info("After ending the conversation above, copy the transcript and paste it here:")
        
        transcript_input = st.text_area(
            "Paste Transcript JSON",
            height=200,
            placeholder='[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]',
            key="transcript_input"
        )
        
        if st.button("✨ Generate Feedback", type="primary", use_container_width=True):
            if transcript_input:
                try:
                    transcript_data = json.loads(transcript_input)
                    if len(transcript_data) > 0:
                        self.generate_feedback(transcript_data)
                    else:
                        st.warning("Transcript is empty")
                except json.JSONDecodeError as e:
                    st.error(f"Invalid JSON format: {e}")
            else:
                st.warning("Please paste the transcript JSON first")

if __name__ == "__main__":
    app = VPERealtimeApp()
    app.run()