# app.py - Using GPT-4o Audio (native audio in/out)

import streamlit as st
from openai import OpenAI
import base64
import io

# Configuration
ASSISTANT_MAP = {
    "Mrs. Miller (High Value Care 04)": "asst_pWDA8oyZfpvRGWyYDoWhakj1",
}

FEEDBACK_ASSISTANTS = {
    "Mrs. Miller Feedback": "asst_J2yNXKyAVxZ9yhxVD1o4roNh",
}

# Audio model config
AUDIO_MODEL = "gpt-4o-audio-preview"
VOICE = "nova"  # alloy, echo, fable, onyx, nova, shimmer
AUDIO_FORMAT = "mp3"  # wav, mp3, flac, opus, pcm16

MIN_MESSAGES_FOR_FEEDBACK = 3

class VPEAudioApp:
    def __init__(self):
        self.setup_openai()
        self.init_session_state()
        self.load_system_prompt()
    
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
        if "conversation_history" not in st.session_state:
            st.session_state.conversation_history = []
    
    def load_system_prompt(self):
        """Load Mrs. Miller's character instructions from the assistant."""
        # You'll want to fetch the actual instructions from your assistant
        # For now, using a placeholder
        self.system_prompt = """You are Mrs. Miller, a 67-year-old woman presenting for a follow-up visit for a high value care case.

You are concerned about your health and recent test results. Respond naturally and conversationally to the medical student's questions. Stay in character and provide realistic responses based on your medical history.

Be cooperative but naturally concerned. Answer questions thoughtfully, and feel free to ask clarifying questions if needed."""
    
    def audio_to_base64(self, audio_file):
        """Convert uploaded audio file to base64."""
        try:
            audio_bytes = audio_file.read()
            audio_file.seek(0)  # Reset file pointer
            return base64.b64encode(audio_bytes).decode('utf-8')
        except Exception as e:
            st.error(f"Failed to process audio: {e}")
            return None
    
    def send_audio_message(self, audio_base64=None, text_content=None):
        """Send message with audio input/output using Chat Completions API."""
        try:
            # Build the user message
            if audio_base64:
                user_message = {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_base64,
                                "format": "wav"  # or detect from file
                            }
                        }
                    ]
                }
            else:
                user_message = {
                    "role": "user",
                    "content": text_content
                }
            
            # Add to conversation history
            st.session_state.conversation_history.append(user_message)
            
            # Call API with audio modalities
            response = self.client.chat.completions.create(
                model=AUDIO_MODEL,
                modalities=["text", "audio"],
                audio={
                    "voice": VOICE,
                    "format": AUDIO_FORMAT
                },
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *st.session_state.conversation_history
                ]
            )
            
            # Extract response
            assistant_message = response.choices[0].message
            
            # Get text transcript
            text_response = assistant_message.content if assistant_message.content else "[Audio response]"
            
            # Get audio data
            audio_data = None
            if hasattr(assistant_message, 'audio') and assistant_message.audio:
                if hasattr(assistant_message.audio, 'data'):
                    # Audio is base64 encoded
                    audio_data = base64.b64decode(assistant_message.audio.data)
                    # Get transcript from audio if available
                    if hasattr(assistant_message.audio, 'transcript'):
                        text_response = assistant_message.audio.transcript
            
            # Add assistant response to history
            st.session_state.conversation_history.append({
                "role": "assistant",
                "content": text_response
            })
            
            return text_response, audio_data
            
        except Exception as e:
            st.error(f"Failed to get response: {e}")
            return None, None
    
    def generate_feedback(self):
        """Generate feedback using the Assistants API."""
        if len(st.session_state.messages) < MIN_MESSAGES_FOR_FEEDBACK:
            st.warning(f"Need at least {MIN_MESSAGES_FOR_FEEDBACK} message exchanges for feedback")
            return
        
        # Build transcript from display messages
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
            import time
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
            1. Record audio or type your questions
            2. Mrs. Miller responds naturally with audio
            3. Continue the clinical interview
            4. Generate feedback when complete
            """)
            
            st.markdown("---")
            
            if st.button("🔄 Start New Conversation", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation_history = []
                st.rerun()
            
            st.markdown("---")
            st.caption("🎯 Using GPT-4o Audio (native speech)")
        
        # Display conversation history
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
                # Play audio if available
                if msg["role"] == "assistant" and "audio" in msg and msg["audio"]:
                    st.audio(msg["audio"], format=f"audio/{AUDIO_FORMAT}")
        
        # Input sections
        st.markdown("### 🎤 Speak or Type Your Question")
        
        # Audio input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            audio_file = st.file_uploader(
                "Upload audio recording", 
                type=['wav', 'mp3', 'm4a', 'webm', 'ogg'],
                help="Record your question using your device",
                key=f"audio_{len(st.session_state.messages)}"
            )
        
        with col2:
            st.info("💡 Use phone or computer recorder")
        
        if audio_file:
            with st.spinner("🎧 Processing audio..."):
                audio_base64 = self.audio_to_base64(audio_file)
                
                if audio_base64:
                    # Send audio to model
                    text_response, audio_response = self.send_audio_message(audio_base64=audio_base64)
                    
                    if text_response:
                        # Add user message (show transcription)
                        st.session_state.messages.append({
                            "role": "user",
                            "content": "[Audio question]"
                        })
                        
                        # Add assistant response
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": text_response,
                            "audio": audio_response
                        })
                        
                        st.rerun()
        
        # Text input
        st.markdown("### ⌨️ Or Type Your Message")
        if prompt := st.chat_input("Type your message here..."):
            # Send text message
            with st.spinner("💬 Mrs. Miller is responding..."):
                text_response, audio_response = self.send_audio_message(text_content=prompt)
                
                if text_response:
                    # Add messages to display
                    st.session_state.messages.append({
                        "role": "user",
                        "content": prompt
                    })
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": text_response,
                        "audio": audio_response
                    })
                    
                    st.rerun()
        
        # Feedback section
        user_messages = len([m for m in st.session_state.messages if m['role'] == 'user'])
        
        if user_messages >= MIN_MESSAGES_FOR_FEEDBACK:
            st.markdown("---")
            st.subheader("🧠 Ready for Feedback?")
            st.info(f"You've asked {user_messages} questions")
            
            if st.button("✨ Generate Comprehensive Feedback", type="primary", use_container_width=True):
                self.generate_feedback()
        elif user_messages > 0:
            st.info(f"💬 Continue the interview ({user_messages}/{MIN_MESSAGES_FOR_FEEDBACK} exchanges needed)")

if __name__ == "__main__":
    app = VPEAudioApp()
    app.run()