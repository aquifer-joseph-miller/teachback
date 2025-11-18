# app.py - Hybrid Realtime + Assistants API version

import streamlit as st
import openai
import time
import json
from streamlit.components.v1 import html

# Simplified configurations for Mrs. Miller only
ASSISTANT_MAP = {
    "Mrs. Miller (High Value Care 04)": "asst_pWDA8oyZfpvRGWyYDoWhakj1",
}

FEEDBACK_ASSISTANTS = {
    "Mrs. Miller Feedback": "asst_J2yNXKyAVxZ9yhxVD1o4roNh",
}

# Realtime API configuration
REALTIME_MODEL = "gpt-4o-realtime-preview-2024-12-17"
REALTIME_VOICE = "sage"  # Options: alloy, echo, fable, onyx, nova, shimmer, sage

# Configuration
MIN_MESSAGES_FOR_FEEDBACK = 3  # Reduced since audio conversations might be shorter
POLLING_INTERVAL = 2
FEEDBACK_TIMEOUT = 180

class VPERealtimeApp:
    def __init__(self):
        self.setup_openai()
        self.init_session_state()
    
    def setup_openai(self):
        """Initialize OpenAI client with API key from secrets."""
        try:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            self.api_key = st.secrets["OPENAI_API_KEY"]
        except KeyError:
            st.error("OpenAI API key not found in secrets. Please configure OPENAI_API_KEY.")
            st.stop()
    
    def init_session_state(self):
        """Initialize session state variables."""
        if "conversation_transcript" not in st.session_state:
            st.session_state.conversation_transcript = []
        if "realtime_session_id" not in st.session_state:
            st.session_state.realtime_session_id = None
        if "audio_mode" not in st.session_state:
            st.session_state.audio_mode = True
        if "conversation_ended" not in st.session_state:
            st.session_state.conversation_ended = False
    
    def create_realtime_session(self):
        """Create a new Realtime API session with Mrs. Miller's instructions."""
        try:
            # Get Mrs. Miller's assistant instructions
            # Note: You'll need to fetch the actual instructions from the assistant
            patient_instructions = """You are Mrs. Miller, a 67-year-old woman presenting for a follow-up visit. 
You are concerned about your health and recent test results. 
Respond naturally to the medical student's questions in a conversational manner.
Stay in character and provide realistic responses based on your medical history."""
            
            response = openai.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "OpenAI-Beta": "realtime=v1"
                },
                json={
                    "model": REALTIME_MODEL,
                    "voice": REALTIME_VOICE,
                    "instructions": patient_instructions,
                    "modalities": ["audio", "text"],
                    "temperature": 0.8,
                }
            )
            
            session_data = response.json()
            return session_data.get("client_secret", {}).get("value")
            
        except Exception as e:
            st.error(f"Failed to create Realtime session: {e}")
            return None
    
    def get_realtime_audio_component(self, ephemeral_key):
        """Generate HTML component for Realtime API audio interface."""
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .audio-controls {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 20px;
                    padding: 30px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                
                .status {{
                    font-size: 18px;
                    font-weight: bold;
                    color: white;
                    text-align: center;
                }}
                
                .button-container {{
                    display: flex;
                    gap: 15px;
                }}
                
                button {{
                    padding: 15px 30px;
                    font-size: 16px;
                    border: none;
                    border-radius: 25px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: bold;
                }}
                
                #startBtn {{
                    background-color: #4CAF50;
                    color: white;
                }}
                
                #startBtn:hover {{
                    background-color: #45a049;
                    transform: scale(1.05);
                }}
                
                #startBtn:disabled {{
                    background-color: #cccccc;
                    cursor: not-allowed;
                    transform: scale(1);
                }}
                
                #stopBtn {{
                    background-color: #f44336;
                    color: white;
                }}
                
                #stopBtn:hover {{
                    background-color: #da190b;
                    transform: scale(1.05);
                }}
                
                #stopBtn:disabled {{
                    background-color: #cccccc;
                    cursor: not-allowed;
                    transform: scale(1);
                }}
                
                .transcript {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    max-height: 300px;
                    overflow-y: auto;
                    width: 100%;
                    box-shadow: inset 0 2px 10px rgba(0,0,0,0.1);
                }}
                
                .message {{
                    margin: 10px 0;
                    padding: 10px;
                    border-radius: 8px;
                }}
                
                .user {{
                    background-color: #e3f2fd;
                    text-align: right;
                }}
                
                .assistant {{
                    background-color: #f3e5f5;
                    text-align: left;
                }}
                
                .recording {{
                    animation: pulse 1.5s infinite;
                }}
                
                @keyframes pulse {{
                    0%, 100% {{ opacity: 1; }}
                    50% {{ opacity: 0.6; }}
                }}
            </style>
        </head>
        <body>
            <div class="audio-controls">
                <div id="status" class="status">Ready to start conversation</div>
                
                <div class="button-container">
                    <button id="startBtn" onclick="startConversation()">🎤 Start Conversation</button>
                    <button id="stopBtn" onclick="stopConversation()" disabled>⏹️ End Conversation</button>
                </div>
                
                <div class="transcript" id="transcript">
                    <p style="color: #666; text-align: center;">Conversation will appear here...</p>
                </div>
            </div>

            <script>
                let pc = null;
                let dc = null;
                let isConnected = false;
                const ephemeralKey = "{ephemeral_key}";
                
                async function startConversation() {{
                    try {{
                        document.getElementById('startBtn').disabled = true;
                        document.getElementById('status').textContent = 'Connecting...';
                        
                        // Create peer connection
                        pc = new RTCPeerConnection();
                        
                        // Set up audio
                        const ms = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                        ms.getTracks().forEach(track => pc.addTrack(track, ms));
                        
                        // Set up data channel for events
                        dc = pc.createDataChannel('oai-events');
                        dc.addEventListener('message', handleDataChannelMessage);
                        
                        // Handle connection state
                        pc.onconnectionstatechange = () => {{
                            console.log('Connection state:', pc.connectionState);
                            if (pc.connectionState === 'connected') {{
                                isConnected = true;
                                document.getElementById('status').textContent = '🎤 Connected - Speak with Mrs. Miller';
                                document.getElementById('status').classList.add('recording');
                                document.getElementById('stopBtn').disabled = false;
                            }}
                        }};
                        
                        // Create and set local offer
                        const offer = await pc.createOffer();
                        await pc.setLocalDescription(offer);
                        
                        // Send offer to OpenAI Realtime API
                        const response = await fetch('https://api.openai.com/v1/realtime', {{
                            method: 'POST',
                            headers: {{
                                'Authorization': `Bearer ${{ephemeralKey}}`,
                                'Content-Type': 'application/sdp'
                            }},
                            body: offer.sdp
                        }});
                        
                        const answerSdp = await response.text();
                        await pc.setRemoteDescription({{
                            type: 'answer',
                            sdp: answerSdp
                        }});
                        
                    }} catch (error) {{
                        console.error('Error starting conversation:', error);
                        document.getElementById('status').textContent = 'Error: ' + error.message;
                        document.getElementById('startBtn').disabled = false;
                    }}
                }}
                
                function handleDataChannelMessage(event) {{
                    try {{
                        const data = JSON.parse(event.data);
                        console.log('Received event:', data.type);
                        
                        if (data.type === 'conversation.item.created') {{
                            const item = data.item;
                            if (item.type === 'message') {{
                                addMessageToTranscript(item.role, item.content);
                                
                                // Send to Streamlit
                                window.parent.postMessage({{
                                    type: 'transcript_update',
                                    role: item.role,
                                    content: item.content
                                }}, '*');
                            }}
                        }}
                    }} catch (error) {{
                        console.error('Error handling message:', error);
                    }}
                }}
                
                function addMessageToTranscript(role, content) {{
                    const transcript = document.getElementById('transcript');
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `message ${{role}}`;
                    
                    const label = role === 'user' ? 'Student' : 'Mrs. Miller';
                    messageDiv.innerHTML = `<strong>${{label}}:</strong> ${{content}}`;
                    
                    transcript.appendChild(messageDiv);
                    transcript.scrollTop = transcript.scrollHeight;
                }}
                
                function stopConversation() {{
                    if (pc) {{
                        pc.close();
                        pc = null;
                    }}
                    if (dc) {{
                        dc.close();
                        dc = null;
                    }}
                    
                    isConnected = false;
                    document.getElementById('status').textContent = 'Conversation ended';
                    document.getElementById('status').classList.remove('recording');
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                    
                    // Notify Streamlit that conversation ended
                    window.parent.postMessage({{
                        type: 'conversation_ended'
                    }}, '*');
                }}
            </script>
        </body>
        </html>
        """
        return html_code
    
    def wait_for_run_completion(self, thread_id, run_id, timeout=FEEDBACK_TIMEOUT):
        """Wait for feedback generation to complete."""
        start_time = time.time()
        progress_placeholder = st.empty()
        
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            progress_placeholder.info(f"⏱️ Generating feedback... {elapsed}s elapsed")
            
            try:
                run_status = openai.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run_status.status == "completed":
                    progress_placeholder.empty()
                    return True
                elif run_status.status in ("failed", "cancelled", "expired"):
                    progress_placeholder.empty()
                    st.error(f"Feedback generation failed: {run_status.status}")
                    return False
                
                time.sleep(POLLING_INTERVAL)
            except Exception as e:
                progress_placeholder.empty()
                st.error(f"Error: {e}")
                return False
        
        progress_placeholder.empty()
        st.error("Feedback generation timed out")
        return False
    
    def generate_feedback(self):
        """Generate feedback using Assistants API based on audio transcript."""
        if not st.session_state.conversation_transcript:
            st.error("No conversation to provide feedback on.")
            return
        
        # Format transcript
        transcript = "\n\n".join([
            f"{'STUDENT' if msg['role'] == 'user' else 'MRS. MILLER'}: {msg['content']}"
            for msg in st.session_state.conversation_transcript
        ])
        
        try:
            # Create feedback thread
            feedback_thread = openai.beta.threads.create()
            
            # Prepare feedback prompt
            feedback_prompt = f"""
You are an expert clinical skills rater. Use the five-domain assessment framework.

Transcript of the student's conversation with virtual standardized patient Mrs. Miller:

{transcript}

Please provide comprehensive feedback on the student's performance.
"""
            
            # Send to feedback assistant
            openai.beta.threads.messages.create(
                thread_id=feedback_thread.id,
                role="user",
                content=feedback_prompt
            )
            
            # Generate feedback
            feedback_run = openai.beta.threads.runs.create(
                thread_id=feedback_thread.id,
                assistant_id=FEEDBACK_ASSISTANTS["Mrs. Miller Feedback"]
            )
            
            # Wait for completion
            if self.wait_for_run_completion(feedback_thread.id, feedback_run.id):
                # Get feedback
                messages = openai.beta.threads.messages.list(
                    thread_id=feedback_thread.id,
                    limit=1
                )
                
                if messages.data:
                    feedback_text = messages.data[0].content[0].text.value
                    
                    st.subheader("📋 Comprehensive Feedback")
                    st.markdown("*Feedback from Mrs. Miller encounter*")
                    st.markdown(feedback_text)
                    
                    # Option to download transcript
                    st.download_button(
                        label="📥 Download Transcript",
                        data=transcript,
                        file_name="mrs_miller_transcript.txt",
                        mime="text/plain"
                    )
        
        except Exception as e:
            st.error(f"Failed to generate feedback: {e}")
    
    def run(self):
        """Main application loop."""
        st.set_page_config(
            page_title="Virtual Patient Encounter - Mrs. Miller",
            page_icon="🎤",
            layout="wide"
        )
        
        st.title("🎤 Virtual Patient Encounter - Mrs. Miller")
        st.markdown("*High Value Care Case 04 - Audio Interview*")
        
        # Sidebar info
        with st.sidebar:
            st.header("About This Encounter")
            st.info("""
            **Mrs. Miller** is a 67-year-old woman presenting for a follow-up visit.
            
            **Instructions:**
            1. Click "Start Conversation" to begin
            2. Allow microphone access when prompted
            3. Conduct your patient interview
            4. Click "End Conversation" when finished
            5. Generate feedback to review your performance
            """)
            
            st.markdown("---")
            st.markdown("### Technical Info")
            st.caption("Using OpenAI Realtime API for natural audio conversations")
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("💬 Audio Interview")
            
            # Create or get realtime session
            if not st.session_state.realtime_session_id:
                with st.spinner("Initializing audio session..."):
                    ephemeral_key = self.create_realtime_session()
                    if ephemeral_key:
                        st.session_state.realtime_session_id = ephemeral_key
                        st.success("✅ Audio session ready!")
                    else:
                        st.error("Failed to initialize audio session")
                        st.stop()
            
            # Display audio interface
            if st.session_state.realtime_session_id:
                html_component = self.get_realtime_audio_component(
                    st.session_state.realtime_session_id
                )
                html(html_component, height=500)
        
        with col2:
            st.subheader("📊 Session Info")
            
            if st.session_state.conversation_transcript:
                st.metric(
                    "Messages Exchanged",
                    len(st.session_state.conversation_transcript)
                )
                
                with st.expander("View Transcript", expanded=False):
                    for msg in st.session_state.conversation_transcript:
                        role = "🎓 Student" if msg['role'] == 'user' else "👩‍⚕️ Mrs. Miller"
                        st.markdown(f"**{role}:** {msg['content']}")
            else:
                st.info("Start the conversation to see transcript")
        
        # Feedback section
        st.markdown("---")
        
        if len(st.session_state.conversation_transcript) >= MIN_MESSAGES_FOR_FEEDBACK:
            st.subheader("🧠 Ready for Feedback?")
            
            if st.button("Generate Feedback!", type="primary", use_container_width=True):
                self.generate_feedback()
        else:
            st.info(f"Continue the conversation (need at least {MIN_MESSAGES_FOR_FEEDBACK} exchanges)")
        
        # Listen for messages from iframe
        st.markdown("""
        <script>
        window.addEventListener('message', function(event) {
            if (event.data.type === 'transcript_update') {
                // Send to Streamlit backend
                window.parent.streamlit.setComponentValue({
                    type: 'transcript_update',
                    role: event.data.role,
                    content: event.data.content
                });
            } else if (event.data.type === 'conversation_ended') {
                window.parent.streamlit.setComponentValue({
                    type: 'conversation_ended'
                });
            }
        });
        </script>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    app = VPERealtimeApp()
    app.run()
    