# feedback_assistants.py - Simplified for Mrs. Miller only

FEEDBACK_ASSISTANTS = {
    "Mrs. Miller Feedback": "asst_J2yNXKyAVxZ9yhxVD1o4roNh",
}

def get_feedback_assistant_id(patient_name):
    """Get feedback assistant ID by patient name."""
    feedback_key = f"{patient_name} Feedback"
    return FEEDBACK_ASSISTANTS.get(feedback_key)