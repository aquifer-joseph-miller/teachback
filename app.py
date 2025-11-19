# app.py - Realtime API with WebSocket

import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import time

# Configuration
FEEDBACK_ASSISTANTS = {
    "Mrs. Miller Feedback": "asst_J2yNXKyAVxZ9yhxVD1o4roNh",
}

# Your Mrs. Miller prompt ID from the Realtime API
MRS_MILLER_PROMPT_ID = "pmpt_691cc606dfb4819491acd1328e0488dd0854e783a6e7f3ec"
PROMPT_VERSION = "3"

MIN_MESSAGES_FOR_FEEDBACK = 3

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
            st.error("OpenAI API key not found. Please configure OPENAI_API_KEY in secrets.")
            st.stop()
    
    def init_session_state(self):
        """Initialize session state."""
        if "transcript" not in st.session_state:
            st.session_state.transcript = []
        if "session_active" not in st.session_state:
            st.session_state.session_active = False
    
    def create_realtime_session(self):
        """Create ephemeral token for Realtime API."""
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
                    "model": "gpt-4o-realtime-preview-2024-12-17",
                    "voice": "sage"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("client_secret", {}).get("value")
            else:
                st.error(f"Failed to create session: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Error creating session: {e}")
            return None
    
    def realtime_component(self, ephemeral_token):
        """Create the Realtime API WebSocket component."""
        
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
                    max-width: 800px;
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
                    margin-bottom: 30px;
                    padding: 20px;
                    border-radius: 10px;
                    background: #f0f0f0;
                }}
                
                .status.connected {{
                    background: #4CAF50;
                    color: white;
                    animation: pulse 2s infinite;
                }}
                
                .status.disconnected {{
                    background: #f44336;
                    color: white;
                }}
                
                .controls {{
                    display: flex;
                    gap: 15px;
                    justify-content: center;
                    margin-bottom: 30px;
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
                
                button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                }}
                
                #connectBtn {{
                    background: #4CAF50;
                    color: white;
                }}
                
                #disconnectBtn {{
                    background: #f44336;
                    color: white;
                }}
                
                #disconnectBtn:disabled,
                #connectBtn:disabled {{
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
                    margin-top: 20px;
                }}
                
                .message {{
                    margin: 15px 0;
                    padding: 15px;
                    border-radius: 10px;
                    line-height: 1.6;
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
                
                .error {{
                    background: #ffebee;
                    color: #c62828;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 10px 0;
                    border-left: 4px solid #c62828;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2 style="text-align: center; color: #333; margin-bottom: 30px;">
                    🎤 Voice Conversation with Mrs. Miller
                </h2>
                
                <div id="status" class="status">Ready to connect</div>
                
                <div class="controls">
                    <button id="connectBtn" onclick="connectRealtime()">
                        🎤 Start Conversation
                    </button>
                    <button id="disconnectBtn" onclick="disconnectRealtime()" disabled>
                        ⏹️ End Conversation
                    </button>
                </div>
                
                <div id="error" style="display: none;" class="error"></div>
                
                <div class="transcript" id="transcript">
                    <p style="text-align: center; color: #999;">
                        Conversation transcript will appear here...
                    </p>
                </div>
            </div>

            <script>
                let peerConnection = null;
                let dataChannel = null;
                let audioStream = null;
                const ephemeralToken = "{ephemeral_token}";
                
                async function connectRealtime() {{
                    try {{
                        document.getElementById('connectBtn').disabled = true;
                        document.getElementById('status').textContent = 'Requesting microphone access...';
                        document.getElementById('error').style.display = 'none';
                        
                        // Get microphone access
                        audioStream = await navigator.mediaDevices.getUserMedia({{ 
                            audio: {{
                                echoCancellation: true,
                                noiseSuppression: true,
                                autoGainControl: true
                            }}
                        }});
                        
                        document.getElementById('status').textContent = 'Connecting to Mrs. Miller...';
                        
                        // Create peer connection
                        peerConnection = new RTCPeerConnection();
                        
                        // Add audio tracks
                        audioStream.getTracks().forEach(track => {{
                            peerConnection.addTrack(track, audioStream);
                        }});
                        
                        // Handle incoming audio
                        peerConnection.ontrack = (event) => {{
                            const remoteAudio = new Audio();
                            remoteAudio.srcObject = event.streams[0];
                            remoteAudio.play();
                        }};
                        
                        // Set up data channel for events
                        dataChannel = peerConnection.createDataChannel('oai-events');
                        
                        dataChannel.onopen = () => {{
                            console.log('Data channel opened');
                        }};
                        
                        dataChannel.onmessage = (event) => {{
                            handleRealtimeEvent(event.data);
                        }};
                        
                        // Connection state handling
                        peerConnection.onconnectionstatechange = () => {{
                            console.log('Connection state:', peerConnection.connectionState);
                            
                            if (peerConnection.connectionState === 'connected') {{
                                document.getElementById('status').textContent = '🎤 Connected - Speaking with Mrs. Miller';
                                document.getElementById('status').className = 'status connected';
                                document.getElementById('disconnectBtn').disabled = false;
                            }} else if (peerConnection.connectionState === 'disconnected' || 
                                       peerConnection.connectionState === 'failed') {{
                                showError('Connection lost. Please try again.');
                                disconnectRealtime();
                            }}
                        }};
                        
                        // Create offer
                        const offer = await peerConnection.createOffer();
                        await peerConnection.setLocalDescription(offer);
                        
                        // Send offer to OpenAI Realtime API
                        const response = await fetch('https://api.openai.com/v1/realtime', {{
                            method: 'POST',
                            headers: {{
                                'Authorization': `Bearer ${{ephemeralToken}}`,
                                'Content-Type': 'application/sdp'
                            }},
                            body: offer.sdp
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP ${{response.status}}: ${{await response.text()}}`);
                        }}
                        
                        const answerSdp = await response.text();
                        
                        await peerConnection.setRemoteDescription({{
                            type: 'answer',
                            sdp: answerSdp
                        }});
                        
                    }} catch (error) {{
                        console.error('Error connecting:', error);
                        showError('Failed to connect: ' + error.message);
                        document.getElementById('connectBtn').disabled = false;
                        document.getElementById('status').textContent = 'Connection failed';
                        document.getElementById('status').className = 'status disconnected';
                    }}
                }}
                
                function handleRealtimeEvent(data) {{
                    try {{
                        const event = JSON.parse(data);
                        console.log('Realtime event:', event.type);
                        
                        // Handle conversation item creation (messages)
                        if (event.type === 'conversation.item.created') {{
                            const item = event.item;
                            
                            if (item.type === 'message' && item.role && item.content) {{
                                const role = item.role;
                                const content = Array.isArray(item.content) 
                                    ? item.content.map(c => c.text || c.transcript || '').join(' ')
                                    : item.content;
                                
                                if (content) {{
                                    addToTranscript(role, content);
                                    
                                    // Send to Streamlit
                                    window.parent.postMessage({{
                                        type: 'transcript_update',
                                        role: role,
                                        content: content
                                    }}, '*');
                                }}
                            }}
                        }}
                        
                        // Handle response audio transcript
                        if (event.type === 'response.audio_transcript.done') {{
                            if (event.transcript) {{
                                addToTranscript('assistant', event.transcript);
                                
                                window.parent.postMessage({{
                                    type: 'transcript_update',
                                    role: 'assistant',
                                    content: event.transcript
                                }}, '*');
                            }}
                        }}
                        
                        // Handle input audio transcript
                        if (event.type === 'conversation.item.input_audio_transcription.completed') {{
                            if (event.transcript) {{
                                addToTranscript('user', event.transcript);
                                
                                window.parent.postMessage({{
                                    type: 'transcript_update',
                                    role: 'user',
                                    content: event.transcript
                                }}, '*');
                            }}
                        }}
                        
                    }} catch (error) {{
                        console.error('Error handling event:', error);
                    }}
                }}
                
                function addToTranscript(role, content) {{
                    const transcript = document.getElementById('transcript');
                    
                    // Clear initial message
                    if (transcript.children.length === 1 && 
                        transcript.children[0].tagName === 'P') {{
                        transcript.innerHTML = '';
                    }}
                    
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${{role}}`;
                    
                    const speakerDiv = document.createElement('div');
                    speakerDiv.className = 'speaker';
                    speakerDiv.textContent = role === 'user' ? '🎓 Student' : '👩‍⚕️ Mrs. Miller';
                    
                    const contentDiv = document.createElement('div');
                    contentDiv.textContent = content;
                    
                    messageDiv.appendChild(speakerDiv);
                    messageDiv.appendChild(contentDiv);
                    transcript.appendChild(messageDiv);
                    
                    // Scroll to bottom
                    transcript.scrollTop = transcript.scrollHeight;
                }}
                
                function disconnectRealtime() {{
                    if (audioStream) {{
                        audioStream.getTracks().forEach(track => track.stop());
                        audioStream = null;
                    }}
                    
                    if (dataChannel) {{
                        dataChannel.close();
                        dataChannel = null;
                    }}
                    
                    if (peerConnection) {{
                        peerConnection.close();
                        peerConnection = null;
                    }}
                    
                    document.getElementById('status').textContent = 'Disconnected';
                    document.getElementById('status').className = 'status disconnected';
                    document.getElementById('connectBtn').disabled = false;
                    document.getElementById('disconnectBtn').disabled = true;
                    
                    // Notify Streamlit
                    window.parent.postMessage({{
                        type: 'conversation_ended'
                    }}, '*');
                }}
                
                function showError(message) {{
                    const errorDiv = document.getElementById('error');
                    errorDiv.textContent = message;
                    errorDiv.style.display = 'block';
                }}
            </script>
        </body>
        </html>
        """
        
        return component_html
    
    def generate_feedback(self):
        """Generate feedback from transcript."""
        if len(st.session_state.transcript) < MIN_MESSAGES_FOR_FEEDBACK:
            st.warning(f"Need at least {MIN_MESSAGES_FOR_FEEDBACK} exchanges for feedback")
            return
        
        # Build transcript
        transcript = "\n\n".join([
            f"{'STUDENT' if msg['role'] == 'user' else 'MRS. MILLER'}: {msg['content']}"
            for msg in st.session_state.transcript
        ])
        
        try:
            feedback_thread = self.client.beta.threads.create()
            
            feedback_prompt = f"""You are an expert clinical skills rater. Use the five-domain assessment framework.

Transcript of the student's conversation with virtual standardized patient Mrs. Miller:

{transcript}

Please provide comprehensive feedback on the student's performance."""
            
            self.client.beta.threads.messages.create(
                thread_id=feedback_thread.id,
                role="user",
                content=feedback_prompt
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=feedback_thread.id,
                assistant_id=FEEDBACK_ASSISTANTS["Mrs. Miller Feedback"]
            )
            
            with st.spinner("🧠 Generating comprehensive feedback..."):
                while True:
                    run_status = self.client.beta.threads.runs.retrieve(
                        thread_id=feedback_thread.id,
                        run_id=run.id
                    )
                    
                    if run_status.status == "completed":
                        break
                    elif run_status.status in ["failed", "cancelled", "expired"]:
                        st.error(f"Feedback generation failed: {run_status.status}")
                        return
                    
                    time.sleep(2)
                
                messages = self.client.beta.threads.messages.list(
                    thread_id=feedback_thread.id,
                    limit=1
                )
                
                if messages.data:
                    feedback_text = messages.data[0].content[0].text.value
                    
                    st.subheader("📋 Comprehensive Feedback")
                    st.markdown(feedback_text)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Download Transcript",
                            transcript,
                            file_name="transcript.txt",
                            mime="text/plain"
                        )
                    with col2:
                        st.download_button(
                            "📥 Download Feedback",
                            feedback_text,
                            file_name="feedback.txt",
                            mime="text/plain"
                        )
        
        except Exception as e:
            st.error(f"Failed to generate feedback: {e}")
    
    def run(self):
        """Main application."""
        st.set_page_config(
            page_title="VPE - Mrs. Miller (Realtime)",
            page_icon="🎤",
            layout="wide"
        )
        
        st.title("🎤 Virtual Patient Encounter - Mrs. Miller")
        st.markdown("*High Value Care Case 04 - Real-time Voice Conversation*")
        
        # Sidebar
        with st.sidebar:
            st.header("About This Encounter")
            st.info("""
            **Mrs. Miller** is a 67-year-old woman presenting for a follow-up visit.
            
            **Instructions:**
            1. Click "Start Conversation"
            2. Allow microphone access
            3. Speak naturally with Mrs. Miller
            4. Click "End Conversation" when done
            5. Generate feedback
            """)
            
            st.markdown("---")
            
            if st.button("🔄 New Session", use_container_width=True):
                st.session_state.transcript = []
                st.rerun()
            
            st.markdown("---")
            
            if st.session_state.transcript:
                st.metric("Messages", len(st.session_state.transcript))
                
                with st.expander("View Transcript"):
                    for msg in st.session_state.transcript:
                        role = "🎓 Student" if msg['role'] == 'user' else "👩‍⚕️ Mrs. Miller"
                        st.markdown(f"**{role}:** {msg['content']}")
            
            st.caption("🎯 Using OpenAI Realtime API")
        
        # Create session and show component
        with st.spinner("🔄 Initializing voice session..."):
            ephemeral_token = self.create_realtime_session()
        
        if ephemeral_token:
            st.success("✅ Voice session ready!")
            
            # Display the realtime component
            html_code = self.realtime_component(ephemeral_token)
            components.html(html_code, height=700, scrolling=True)
        else:
            st.error("Failed to initialize voice session. Please refresh the page.")
            st.stop()
        
        # Feedback section
        if len(st.session_state.transcript) >= MIN_MESSAGES_FOR_FEEDBACK:
            st.markdown("---")
            st.subheader("🧠 Ready for Feedback?")
            
            if st.button("✨ Generate Comprehensive Feedback", type="primary", use_container_width=True):
                self.generate_feedback()

if __name__ == "__main__":
    app = VPERealtimeApp()
    app.run()