# app.py - Streamlit app with custom VPE component

import streamlit as st
from openai import OpenAI
import time
import json

from vpe_component import vpe_component  # ✅ use our custom component wrapper


# ---------- Configuration ----------

FEEDBACK_ASSISTANTS = {
    "Mrs. Miller Feedback": "asst_J2yNXKyAVxZ9yhxVD1o4roNh",
}

MRS_MILLER_PROMPT_ID = "pmpt_691cc606dfb4819491acd1328e0488dd0854e783a6e7f3ec"
PROMPT_VERSION = "4"


# ---------- App class ----------

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
            st.error("OpenAI API key not found in st.secrets['OPENAI_API_KEY'].")
            st.stop()

    def init_session_state(self):
        if "feedback_done" not in st.session_state:
            st.session_state.feedback_done = False
        if "last_transcript_text" not in st.session_state:
            st.session_state.last_transcript_text = None
        if "last_feedback_text" not in st.session_state:
            st.session_state.last_feedback_text = None

    # ---------- Realtime session ----------

    def create_realtime_session(self):
        """Create ephemeral token with input transcription enabled."""
        try:
            import requests

            response = requests.post(
                "https://api.openai.com/v1/realtime/sessions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "OpenAI-Beta": "realtime=v1",
                },
                json={
                    "prompt": {
                        "id": MRS_MILLER_PROMPT_ID,
                        "version": PROMPT_VERSION,
                    },
                    "input_audio_transcription": {
                        "model": "whisper-1",
                    },
                },
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("client_secret", {}).get("value")
            else:
                st.error(
                    f"Realtime session failed: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            st.error(f"Error creating realtime session: {e}")
            return None

    # ---------- Feedback generation ----------

    def generate_feedback(self, transcript_data):
        """Call the Assistant API to generate feedback and cache it."""
        transcript_text = "\n\n".join(
            [
                f"{'STUDENT' if msg.get('role') == 'user' else 'MRS. MILLER'}: {msg.get('content', '')}"
                for msg in transcript_data
            ]
        )

        try:
            feedback_thread = self.client.beta.threads.create()

            self.client.beta.threads.messages.create(
                thread_id=feedback_thread.id,
                role="user",
                content=f"""You are an expert clinical skills rater. Use the five-domain assessment framework.

Transcript:

{transcript_text}

Provide comprehensive feedback.""",
            )

            run = self.client.beta.threads.runs.create(
                thread_id=feedback_thread.id,
                assistant_id=FEEDBACK_ASSISTANTS["Mrs. Miller Feedback"],
            )

            while True:
                status = self.client.beta.threads.runs.retrieve(
                    thread_id=feedback_thread.id,
                    run_id=run.id,
                )

                if status.status == "completed":
                    break
                elif status.status in ["failed", "cancelled", "expired"]:
                    st.error(f"Feedback generation failed: {status.status}")
                    return

                time.sleep(2)

            messages = self.client.beta.threads.messages.list(
                thread_id=feedback_thread.id, limit=1
            )

            if messages.data:
                feedback = messages.data[0].content[0].text.value

                st.session_state.last_transcript_text = transcript_text
                st.session_state.last_feedback_text = feedback
                st.session_state.feedback_done = True

        except Exception as e:
            st.error(f"Error generating feedback: {e}")

    def render_cached_feedback(self):
        transcript_text = st.session_state.last_transcript_text
        feedback = st.session_state.last_feedback_text

        if not transcript_text or not feedback:
            st.warning("No feedback available yet.")
            return

        st.markdown("### 📝 Conversation Transcript")
        with st.expander("View Full Transcript"):
            st.text_area(
                "",
                transcript_text,
                height=200,
                key="transcript_display",
            )

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
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "📥 Download Feedback",
                feedback,
                file_name="feedback.txt",
                use_container_width=True,
            )

    # ---------- Main app ----------

    def run(self):
        st.set_page_config(
            page_title="VPE - Mrs. Miller",
            page_icon="🎤",
            layout="wide",
        )

        st.title("🎤 Virtual Patient Encounter - Mrs. Miller")
        st.markdown("*High Value Care Case 04*")

        with st.sidebar:
            st.header("Instructions")
            st.info(
                """
                1. Click **"Start Conversation"** in the widget  
                2. Allow microphone access  
                3. Speak with Mrs. Miller  
                4. Click **"End Conversation"**  
                5. The transcript is sent back to Streamlit automatically  
                6. Feedback will appear below
                """
            )

            if st.button("🔄 Reset Session", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.experimental_rerun()

        # ----- Voice component -----
        ephemeral_token = self.create_realtime_session()

        transcript = None
        if ephemeral_token:
            st.success("✅ Voice session ready!")
            transcript = vpe_component(
                ephemeralToken=ephemeral_token,
                key="vpe_component",
            )
        else:
            st.error("Could not create realtime session. Check your API key and network.")

        st.markdown("---")

        # transcript will be:
        # - None until the conversation is ended in the component
        # - A Python list of {role, content} once Streamlit.setComponentValue is called
        if transcript is not None and not st.session_state.get("feedback_done", False):
            # Ensure it's the right type (should already be a list of dicts)
            try:
                if isinstance(transcript, str):
                    transcript_data = json.loads(transcript)
                else:
                    transcript_data = transcript

                with st.spinner("🧠 Generating comprehensive feedback..."):
                    self.generate_feedback(transcript_data)
            except Exception as e:
                st.error(f"Error using transcript from component: {e}")

        if st.session_state.get("feedback_done"):
            self.render_cached_feedback()


if __name__ == "__main__":
    app = VPERealtimeApp()
    app.run()
