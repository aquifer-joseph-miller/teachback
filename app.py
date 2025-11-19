# app.py - Fixed version

import streamlit as st
from openai import OpenAI
import time

# Configuration
ASSISTANT_MAP = {
    "Mrs. Miller (High Value Care 04)": "asst_pWDA8oyZfpvRGWyYDoWhakj1",
}

FEEDBACK_ASSISTANTS = {
    "Mrs. Miller Feedback": "asst_J2yNXKyAVxZ9yhxVD1o4roNh",
}

MIN_MESSAGES_FOR_FEEDBACK = 3
POLLING_INTERVAL = 2
FEEDBACK_TIMEOUT = 180
CHAT_TIMEOUT = 90

class VPEAudioApp:
    def __init__(self):
        self.setup_openai()
        self.init_session_state()
    
    def setup_openai(self):
        """Initialize OpenAI client."""
        try:
            self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        except KeyError:
            st.error("OpenAI API key not found. Please configure OPENAI_API_KEY in secrets.")
            st.stop()
    
    def init_session_state(self):
        """Initialize session state."""
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "thread_id" not in st.session_state:
            st.session_state.thread_id = self.create_thread()
        if "audio_enabled" not in st.session_state:
            st.session_state.audio_enabled = True
    
    def create_thread(self):
        """Create a new OpenAI thread."""
        try:
            thread = self.client.beta.threads.create()
            return thread.id
        except Exception as e:
            st.error(f"Failed to create thread: {e}")
            st.stop()
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio using Whisper API."""
        try:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text
        except Exception as e:
            st.error(f"Transcription failed: {e}")
            return None
    
    def text_to_speech(self, text):
        """Convert text to speech using OpenAI TTS."""
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=text
            )
            return response.content
        except Exception as e:
            st.error(f"Text-to-speech failed: {e}")
            return None
    
    def wait_for_run_completion(self, thread_id, run_id, timeout, operation="operation"):
        """Wait for run to complete with progress indicator."""
        start_time = time.time()
        progress_placeholder = st.empty()
        
        while time.time() - start_time < timeout:
            elapsed = int(time.time() - start_time)
            progress_placeholder.info(f"⏱️ {operation.title()}... {elapsed}s")
            
            try:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                
                if run_status.status == "completed":
                    progress_placeholder.empty()
                    return True
                elif run_status.status in ("failed", "cancelled", "expired"):
                    progress_placeholder.empty()
                    st.error(f"{operation.title()} failed: {run_status.status}")
                    return False
                
                time.sleep(POLLING_INTERVAL)
            except Exception as e:
                progress_placeholder.empty()
                st.error(f"Error: {e}")
                return False
        
        progress_placeholder.empty()
        st.error(f"{operation.title()} timed out")
        return False
    
    def send_message_to_patient(self, prompt, assistant_id):
        """Send message to virtual patient."""
        try:
            # Add message to thread
            self.client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=prompt
            )
            
            # Create run
            run = self.client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=assistant_id
            )
            
            # Wait for completion
            if not self.wait_for_run_completion(
                st.session_state.thread_id, 
                run.id, 
                CHAT_TIMEOUT, 
                "getting response"
            ):
                return None
            
            # Get response
            messages = self.client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id,
                limit=1
            )
            
            if messages.data:
                return messages.data[0].content[0].text.value
            return None
            
        except Exception as e:
            st.error(f"Failed to send message: {e}")
            return None
    
    def generate_feedback(self):
        """Generate feedback from conversation transcript."""
        if len(st.session_state.messages) < MIN_MESSAGES_FOR_FEEDBACK:
            st.warning(f"Need at least {MIN_MESSAGES_FOR_FEEDBACK} messages for feedback")
            return
        
        # Build transcript
        transcript = "\n\n".join([
            f"{'STUDENT' if msg['role'] == 'user' else 'MRS. MILLER'}: {msg['content']}"
            for msg in st.session_state.messages
        ])
        
        try:
            # Create feedback thread
            feedback_thread = self.client.beta.threads.create()
            
            # Create feedback prompt
            feedback_prompt = f"""You are an expert clinical skills rater. Use the five-domain assessment framework.

Transcript of the student's conversation with virtual standardized patient Mrs. Miller:

{transcript}

Please provide comprehensive feedback on the student's performance."""
            
            # Send to feedback assistant
            self.client.beta.threads.messages.create(
                thread_id=feedback_thread.id,
                role="user",
                content=feedback_prompt
            )
            
            # Generate feedback
            run = self.client.beta.threads.runs.create(
                thread_id=feedback_thread.id,
                assistant_id=FEEDBACK_ASSISTANTS["Mrs. Miller Feedback"]
            )
            
            # Wait for completion
            if self.wait_for_run_completion(
                feedback_thread.id, 
                run.id, 
                FEEDBACK_TIMEOUT,
                "generating feedback"
            ):
                # Get feedback
                messages = self.client.beta.threads.messages.list(
                    thread_id=feedback_thread.id,
                    limit=1
                )
                
                if messages.data:
                    feedback_text = messages.data[0].content[0].text.value
                    
                    st.subheader("📋 Comprehensive Feedback")
                    st.markdown("*Feedback from Mrs. Miller encounter*")
                    st.markdown(feedback_text)
                    
                    # Download options
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
            page_title="VPE - Mrs. Miller",
            page_icon="🎤",
            layout="wide"
        )
        
        st.title("🎤 Virtual Patient Encounter - Mrs. Miller")
        st.markdown("*High Value Care Case 04 - Audio Interview*")
        
        # Sidebar
        with st.sidebar:
            st.header("About This Encounter")
            st.info("""
            **Mrs. Miller** is a 67-year-old woman presenting for a follow-up visit.
            
            **Instructions:**
            1. Record or type your questions
            2. Mrs. Miller will respond with audio
            3. Continue the conversation
            4. Generate feedback when done
            """)
            
            st.markdown("---")
            
            st.session_state.audio_enabled = st.checkbox(
                "🔊 Enable Audio Responses", 
                value=st.session_state.audio_enabled,
                help="Mrs. Miller will speak her responses"
            )
            
            if st.button("🔄 Start New Conversation", use_container_width=True):
                st.session_state.messages = []
                st.session_state.thread_id = self.create_thread()
                st.rerun()
            
            st.markdown("---")
            st.caption("Using OpenAI Whisper + TTS")
        
        # Main area
        assistant_id = ASSISTANT_MAP["Mrs. Miller (High Value Care 04)"]
        
        # Display chat history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                # Play audio if available
                if msg["role"] == "assistant" and "audio" in msg:
                    st.audio(msg["audio"], format="audio/mp3")
        
        # Audio upload section
        st.markdown("### 🎤 Record Your Question")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            audio_file = st.file_uploader(
                "Upload audio recording (WAV, MP3, M4A)", 
                type=['wav', 'mp3', 'm4a', 'ogg'],
                help="Record your question and upload it here",
                key=f"audio_upload_{len(st.session_state.messages)}"
            )
        
        with col2:
            st.info("💡 Use your phone's voice recorder or computer microphone")
        
        if audio_file:
            with st.spinner("🎧 Transcribing your question..."):
                transcript = self.transcribe_audio(audio_file)
                
                if transcript:
                    st.success(f"✅ You said: *\"{transcript}\"*")
                    
                    # Add to chat
                    st.session_state.messages.append({
                        "role": "user",
                        "content": transcript
                    })
                    
                    with st.chat_message("user"):
                        st.markdown(transcript)
                    
                    # Get response
                    with st.spinner("💬 Mrs. Miller is responding..."):
                        response = self.send_message_to_patient(transcript, assistant_id)
                        
                        if response:
                            msg_data = {"role": "assistant", "content": response}
                            
                            # Convert to audio if enabled
                            if st.session_state.audio_enabled:
                                audio_content = self.text_to_speech(response)
                                if audio_content:
                                    msg_data["audio"] = audio_content
                            
                            st.session_state.messages.append(msg_data)
                            st.rerun()
        
        # Text input (always available)
        st.markdown("### ⌨️ Or Type Your Message")
        if prompt := st.chat_input("Type your message here..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            response = self.send_message_to_patient(prompt, assistant_id)
            
            if response:
                msg_data = {"role": "assistant", "content": response}
                
                # Add audio if enabled
                if st.session_state.audio_enabled:
                    audio_content = self.text_to_speech(response)
                    if audio_content:
                        msg_data["audio"] = audio_content
                
                st.session_state.messages.append(msg_data)
                st.rerun()
        
        # Feedback section
        message_pairs = len([m for m in st.session_state.messages if m['role'] == 'user'])
        
        if message_pairs >= MIN_MESSAGES_FOR_FEEDBACK:
            st.markdown("---")
            st.subheader("🧠 Ready for Feedback?")
            st.info(f"You've exchanged {message_pairs} messages with Mrs. Miller")
            
            if st.button("✨ Generate Comprehensive Feedback", type="primary", use_container_width=True):
                self.generate_feedback()
        elif message_pairs > 0:
            st.info(f"💬 Continue the conversation ({message_pairs}/{MIN_MESSAGES_FOR_FEEDBACK} messages needed for feedback)")

if __name__ == "__main__":
    app = VPEAudioApp()
    app.run()