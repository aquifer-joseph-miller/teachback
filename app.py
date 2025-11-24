# app.py - Multi-patient support with Aquifer branding

import streamlit as st
from openai import OpenAI
import streamlit.components.v1 as components
import time
import json
from patient_config import PATIENT_SCENARIOS, get_patient_config, get_all_patients

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
        if "selected_patient" not in st.session_state:
            st.session_state.selected_patient = get_all_patients()[0]
    
    def create_realtime_session(self, patient_config):
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
                        "id": patient_config["prompt_id"],
                        "version": patient_config["prompt_version"]
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
    
    def realtime_component(self, ephemeral_token, patient_config):
        """Create the Realtime API component with Aquifer branding."""
        
        patient_icon = patient_config["icon"]
        patient_name = patient_config["display_name"].split(" - ")[0]
        
        component_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                * {{
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #F8F9FA;
                    min-height: 100vh;
                }}
                
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                }}
                
                .header {{
                    background: linear-gradient(135deg, #1B5599 0%, #2372E0 100%);
                    color: white;
                    padding: 32px;
                    text-align: center;
                }}
                
                .header h2 {{
                    margin: 0;
                    font-family: 'Nunito Sans', sans-serif;
                    font-weight: 700;
                    font-size: 28px;
                    letter-spacing: -0.5px;
                }}
                
                .content {{
                    padding: 32px;
                }}
                
                .status {{
                    text-align: center;
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 24px;
                    padding: 20px;
                    border-radius: 8px;
                    background: #EEF2F6;
                    color: #293346;
                    border: 2px solid #D0DEF4;
                }}
                
                .status.connected {{
                    background: #E8F5E9;
                    color: #2A7937;
                    border-color: #2A7937;
                    animation: pulse 2s infinite;
                }}
                
                .controls {{
                    display: flex;
                    gap: 16px;
                    justify-content: center;
                    margin-bottom: 32px;
                    flex-wrap: wrap;
                }}
                
                button {{
                    padding: 14px 32px;
                    font-size: 16px;
                    font-weight: 600;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    font-family: 'DM Sans', sans-serif;
                    letter-spacing: 0.2px;
                }}
                
                button:hover:not(:disabled) {{
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }}
                
                button:active:not(:disabled) {{
                    transform: translateY(0);
                }}
                
                #connectBtn {{
                    background: #2372E0;
                    color: white;
                }}
                
                #connectBtn:hover:not(:disabled) {{
                    background: #1B5599;
                }}
                
                #disconnectBtn {{
                    background: #D04900;
                    color: white;
                }}
                
                #disconnectBtn:hover:not(:disabled) {{
                    background: #A03700;
                }}
                
                button:disabled {{
                    background: #6B7682;
                    color: white;
                    cursor: not-allowed;
                    opacity: 0.5;
                    transform: none;
                }}
                
                .transcript {{
                    background: #F8F9FA;
                    border-radius: 8px;
                    padding: 24px;
                    max-height: 450px;
                    overflow-y: auto;
                    border: 1px solid #E0E4E8;
                }}
                
                .transcript::-webkit-scrollbar {{
                    width: 8px;
                }}
                
                .transcript::-webkit-scrollbar-track {{
                    background: #F0F0F0;
                    border-radius: 4px;
                }}
                
                .transcript::-webkit-scrollbar-thumb {{
                    background: #2372E0;
                    border-radius: 4px;
                }}
                
                .message {{
                    margin: 16px 0;
                    padding: 16px 20px;
                    border-radius: 8px;
                    animation: slideIn 0.3s ease;
                }}
                
                @keyframes slideIn {{
                    from {{
                        opacity: 0;
                        transform: translateY(10px);
                    }}
                    to {{
                        opacity: 1;
                        transform: translateY(0);
                    }}
                }}
                
                .user {{
                    background: #D0DEF4;
                    margin-left: 40px;
                    border-left: 4px solid #2372E0;
                }}
                
                .assistant {{
                    background: #F3E5F5;
                    margin-right: 40px;
                    border-left: 4px solid #AD346A;
                }}
                
                .speaker {{
                    font-weight: 700;
                    margin-bottom: 8px;
                    font-size: 14px;
                    letter-spacing: 0.3px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}
                
                .speaker img {{
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    object-fit: cover;
                }}
                
                .user .speaker {{
                    color: #1B5599;
                }}
                
                .assistant .speaker {{
                    color: #AD346A;
                }}
                
                .message-content {{
                    color: #293346;
                    line-height: 1.6;
                }}
                
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.85; }}
                }}
                
                .debug {{
                    background: #E8F5E9;
                    padding: 6px 10px;
                    margin: 2px 0;
                    font-size: 11px;
                    font-family: 'Courier New', monospace;
                    border-radius: 4px;
                    color: #2A7937;
                    border-left: 3px solid #2A7937;
                }}
                
                #debugLog {{
                    max-height: 120px;
                    overflow-y: auto;
                    border: 1px solid #E0E4E8;
                    border-radius: 6px;
                    padding: 12px;
                    margin: 16px 0;
                    background: white;
                }}
                
                #debugLog::-webkit-scrollbar {{
                    width: 6px;
                }}
                
                #debugLog::-webkit-scrollbar-thumb {{
                    background: #6B7682;
                    border-radius: 3px;
                }}
                
                #copyInstructions {{
                    display: none;
                    background: #FFF9E6;
                    border: 2px solid #D04900;
                    border-radius: 8px;
                    padding: 24px;
                    margin-top: 24px;
                }}
                
                #copyInstructions.show {{
                    display: block;
                    animation: slideIn 0.4s ease;
                }}
                
                #copyInstructions h3 {{
                    margin: 0 0 12px 0;
                    color: #D04900;
                    font-family: 'Nunito Sans', sans-serif;
                }}
                
                .copy-btn {{
                    background: #0095C9;
                    color: white;
                    padding: 12px 24px;
                    margin-top: 12px;
                    border-radius: 8px;
                    font-weight: 600;
                }}
                
                .copy-btn:hover {{
                    background: #007A9E;
                }}
                
                #transcriptOutput {{
                    background: white;
                    border: 1px solid #E0E4E8;
                    padding: 16px;
                    margin: 12px 0;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    max-height: 200px;
                    overflow-y: auto;
                    border-radius: 6px;
                    color: #293346;
                }}
                
                .empty-state {{
                    text-align: center;
                    color: #6B7682;
                    padding: 40px 20px;
                    font-size: 15px;
                }}
                
                .empty-state svg {{
                    width: 48px;
                    height: 48px;
                    margin-bottom: 12px;
                    opacity: 0.5;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🎤 Voice Conversation with {patient_name}</h2>
                </div>
                
                <div class="content">
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
                        <div class="empty-state">
                            <div style="font-size: 48px; margin-bottom: 12px;">💬</div>
                            <div>Conversation will appear here...</div>
                        </div>
                    </div>
                    
                    <div id="copyInstructions">
                        <h3>📋 Transcript Ready!</h3>
                        <p><strong>Copy the text below and paste it in the box at the bottom of the page:</strong></p>
                        <div id="transcriptOutput"></div>
                        <button class="copy-btn" onclick="copyTranscript()">📋 Copy to Clipboard</button>
                    </div>
                </div>
            </div>

            <script>
                let peerConnection = null;
                let dataChannel = null;
                let audioStream = null;
                const ephemeralToken = "{ephemeral_token}";
                const patientIcon = "{patient_icon}";
                const patientName = "{patient_name}";
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
                        debugLog('🎤 Requesting microphone access...');
                        
                        audioStream = await navigator.mediaDevices.getUserMedia({{ 
                            audio: {{ echoCancellation: true, noiseSuppression: true }}
                        }});
                        
                        debugLog('✅ Microphone access granted');
                        
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
                        dataChannel.onopen = () => debugLog('📡 Data channel established');
                        dataChannel.onmessage = (event) => handleEvent(event.data);
                        
                        peerConnection.onconnectionstatechange = () => {{
                            if (peerConnection.connectionState === 'connected') {{
                                document.getElementById('status').textContent = '🎤 Connected - Speak now';
                                document.getElementById('status').className = 'status connected';
                                document.getElementById('disconnectBtn').disabled = false;
                                debugLog('🟢 Connection established');
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
                                debugLog('🎓 Student spoke');
                                addMessage('user', text);
                                conversationTranscript.push({{ role: 'user', content: text }});
                            }}
                        }}
                        
                        if (event.type === 'response.audio_transcript.done') {{
                            const text = event.transcript;
                            if (text) {{
                                debugLog('Patient responded');
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
                    if (transcript.querySelector('.empty-state')) {{
                        transcript.innerHTML = '';
                    }}
                    
                    const msg = document.createElement('div');
                    msg.className = `message ${{role}}`;
                    
                    const speaker = document.createElement('div');
                    speaker.className = 'speaker';
                    
                    if (role === 'user') {{
                        speaker.textContent = '🎓 STUDENT';
                    }} else {{
                        speaker.innerHTML = `<img src="${{patientIcon}}" alt="Patient"> ${{patientName.toUpperCase()}}`;
                    }}
                    
                    const text = document.createElement('div');
                    text.className = 'message-content';
                    text.textContent = content;
                    
                    msg.appendChild(speaker);
                    msg.appendChild(text);
                    transcript.appendChild(msg);
                    transcript.scrollTop = transcript.scrollHeight;
                }}
                
                function endConversation() {{
                    debugLog('💾 Ending conversation (' + conversationTranscript.length + ' messages)');
                    
                    if (audioStream) audioStream.getTracks().forEach(t => t.stop());
                    if (dataChannel) dataChannel.close();
                    if (peerConnection) peerConnection.close();
                    
                    document.getElementById('status').textContent = '✓ Conversation Ended';
                    document.getElementById('status').className = 'status';
                    document.getElementById('disconnectBtn').disabled = true;
                    
                    const instructions = document.getElementById('copyInstructions');
                    instructions.className = 'show';
                    
                    const output = document.getElementById('transcriptOutput');
                    output.textContent = JSON.stringify(conversationTranscript, null, 2);
                    
                    debugLog('✅ Transcript ready to copy');
                    
                    instructions.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                }}
                
                function copyTranscript() {{
                    const output = document.getElementById('transcriptOutput');
                    const text = output.textContent;
                    
                    navigator.clipboard.writeText(text).then(() => {{
                        alert('✅ Transcript copied! Scroll down and paste it in the feedback box below.');
                    }}).catch(err => {{
                        alert('Please manually select and copy the text above.');
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        return component_html
    
    def generate_feedback(self, transcript_data, patient_config):
        """Generate feedback from transcript."""
        patient_name = patient_config["display_name"].split(" - ")[0]
        
        transcript_text = "\n\n".join([
            f"{'STUDENT' if msg['role'] == 'user' else patient_name.upper()}: {msg['content']}"
            for msg in transcript_data
        ])
        
        st.markdown("### 📝 Conversation Transcript")
        with st.expander("View Full Transcript", expanded=False):
            st.text_area("", transcript_text, height=200, key="transcript_display", disabled=True)
        
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
                assistant_id=patient_config["feedback_assistant_id"]
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
                        st.error(f"❌ Feedback generation failed: {status.status}")
                        return
                    
                    time.sleep(2)
                
                messages = self.client.beta.threads.messages.list(
                    thread_id=feedback_thread.id,
                    limit=1
                )
                
                if messages.data:
                    feedback = messages.data[0].content[0].text.value
                    
                    st.markdown("---")
                    st.markdown("### 📋 Your Feedback")
                    st.markdown(feedback)
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Download Transcript",
                            transcript_text,
                            file_name=f"transcript_{patient_name.lower().replace(' ', '_')}.txt",
                            use_container_width=True
                        )
                    with col2:
                        st.download_button(
                            "📥 Download Feedback",
                            feedback,
                            file_name=f"feedback_{patient_name.lower().replace(' ', '_')}.txt",
                            use_container_width=True
                        )
        
        except Exception as e:
            st.error(f"❌ Error generating feedback: {e}")
    
    def inject_custom_css(self):
        """Inject Aquifer brand styling."""
        st.markdown("""
        <style>
        /* Import fonts */
        @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;600;700&family=DM+Sans:wght@400;500;600;700&display=swap');
        
        /* Global styles */
        .stApp {
            font-family: 'DM Sans', sans-serif;
        }
        
        /* Headers */
        h1, h2, h3 {
            font-family: 'Nunito Sans', sans-serif;
            color: #1B5599;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1B5599 0%, #2372E0 100%);
        }
        
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        
        [data-testid="stSidebar"] .stSelectbox label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: white !important;
            font-weight: 600;
        }
        
        /* Buttons */
        .stButton > button {
            font-family: 'DM Sans', sans-serif;
            font-weight: 600;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            border: none;
            transition: all 0.2s;
        }
        
        .stButton > button[kind="primary"] {
            background: #2372E0;
            color: white;
        }
        
        .stButton > button[kind="primary"]:hover {
            background: #1B5599;
            box-shadow: 0 4px 12px rgba(35,114,224,0.3);
        }
        
        .stButton > button[kind="secondary"] {
            background: white;
            color: #2372E0;
            border: 2px solid #2372E0;
        }
        
        /* Info boxes */
        .stInfo {
            background-color: #D0DEF4;
            border-left: 4px solid #2372E0;
        }
        
        /* Success boxes */
        .stSuccess {
            background-color: #E8F5E9;
            border-left: 4px solid #2A7937;
        }
        
        /* Text areas */
        .stTextArea textarea {
            font-family: 'Courier New', monospace;
            border: 2px solid #E0E4E8;
            border-radius: 8px;
        }
        
        .stTextArea textarea:focus {
            border-color: #2372E0;
            box-shadow: 0 0 0 1px #2372E0;
        }
        
        /* Expander */
        .streamlit-expanderHeader {
            font-weight: 600;
            color: #293346;
        }
        
        /* Download buttons */
        .stDownloadButton > button {
            background: #0095C9;
            color: white;
        }
        
        .stDownloadButton > button:hover {
            background: #007A9E;
        }
        
        /* Selectbox */
        .stSelectbox > div > div {
            border-color: #E0E4E8;
            border-radius: 8px;
        }
        
        /* Sidebar selectbox - make it more obvious */
        [data-testid="stSidebar"] .stSelectbox > div > div {
            background-color: rgba(255, 255, 255, 0.2) !important;
            border: 2px solid rgba(255, 255, 255, 0.4) !important;
            border-radius: 8px;
            padding: 0.5rem;
            cursor: pointer;
        }
        
        [data-testid="stSidebar"] .stSelectbox > div > div:hover {
            background-color: rgba(255, 255, 255, 0.3) !important;
            border-color: rgba(255, 255, 255, 0.6) !important;
        }
        
        [data-testid="stSidebar"] .stSelectbox svg {
            fill: white !important;
        }
        
        [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] > div {
            background-color: transparent !important;
        }
        
        /* Main title */
        .main h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            letter-spacing: -0.5px;
        }
        
        /* Dividers */
        hr {
            border-color: #E0E4E8;
            margin: 2rem 0;
        }
        
        /* Patient header with icon */
        .patient-header {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 1rem;
        }
        
        .patient-header img {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #2372E0;
        }
        
        .patient-info h1 {
            margin: 0;
            padding: 0;
        }
        
        .patient-info p {
            margin: 0;
            padding: 0;
            color: #6B7682;
            font-style: italic;
        }
        </style>
        """, unsafe_allow_html=True)
    
    def run(self):
        """Main application."""
        st.set_page_config(
            page_title="Virtual Patient Encounters - Aquifer",
            page_icon="🎤",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Inject custom CSS
        self.inject_custom_css()
        
        # Get current patient config
        patient_config = get_patient_config(st.session_state.selected_patient)
        
        # Display patient header with icon
        col1, col2 = st.columns([1, 10])
        with col1:
            st.image(patient_config['icon'], width=80)
        with col2:
            st.title(patient_config['display_name'])
            st.caption(f"*{patient_config['scenario_type']}*")
        
        with st.sidebar:
            st.markdown("## 🏥 Patient Selection")
            st.markdown('<p style="font-size: 0.9rem; margin-bottom: 0.5rem; opacity: 0.9;">Select a patient scenario:</p>', unsafe_allow_html=True)
            
            # Patient selector
            selected = st.selectbox(
                "Choose a patient:",
                options=get_all_patients(),
                index=get_all_patients().index(st.session_state.selected_patient),
                format_func=lambda x: get_patient_config(x)["display_name"],
                label_visibility="collapsed"
            )
            
            # Update if changed
            if selected != st.session_state.selected_patient:
                st.session_state.selected_patient = selected
                st.rerun()
            
            # Show scenario description
            st.info(patient_config["description"])
            
            st.markdown("---")
            st.markdown("## 📋 Instructions")
            st.markdown("""
            **Getting Started:**
            1. Click "Start Conversation"
            2. Allow microphone access  
            3. Speak naturally with the patient
            4. Click "End Conversation" when done
            
            **Getting Feedback:**
            5. Copy the transcript from the yellow box
            6. Paste it in the feedback section below
            7. Click "Generate Feedback"
            """)
            
            st.markdown("---")
            if st.button("🔄 Start New Session", use_container_width=True, type="secondary"):
                for key in list(st.session_state.keys()):
                    if key != "selected_patient":
                        del st.session_state[key]
                st.rerun()
        
        # Show conversation interface
        if st.session_state.conversation_active:
            ephemeral_token = self.create_realtime_session(patient_config)
            
            if ephemeral_token:
                st.success("✅ Voice session ready! Click 'Start Conversation' in the window below.")
                html_code = self.realtime_component(ephemeral_token, patient_config)
                components.html(html_code, height=900, scrolling=True)
        
        # Feedback generation section
        st.markdown("---")
        st.markdown("## 📋 Generate Feedback")
        st.info("💡 **Tip:** After ending your conversation, copy the transcript from the yellow box above and paste it here to receive detailed feedback.")
        
        transcript_input = st.text_area(
            "Paste Transcript JSON",
            height=180,
            placeholder='[{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]',
            key="transcript_input",
            help="Paste the complete JSON transcript from the conversation above"
        )
        
        if st.button("✨ Generate Feedback", type="primary", use_container_width=True):
            if transcript_input:
                try:
                    transcript_data = json.loads(transcript_input)
                    if len(transcript_data) > 0:
                        self.generate_feedback(transcript_data, patient_config)
                    else:
                        st.warning("⚠️ The transcript appears to be empty. Please complete a conversation first.")
                except json.JSONDecodeError as e:
                    st.error(f"❌ Invalid JSON format. Please copy the complete transcript: {e}")
            else:
                st.warning("⚠️ Please paste the transcript JSON first.")

if __name__ == "__main__":
    app = VPERealtimeApp()
    app.run()