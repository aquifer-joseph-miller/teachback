# patient_config.py

PATIENT_SCENARIOS = {
    "Mrs. Miller (High Value Care 04)": {
        "display_name": "Mrs. Miller - Teach Back",
        "scenario_type": "High Value Care",
        "prompt_id": "pmpt_691cc606dfb4819491acd1328e0488dd0854e783a6e7f3ec",
        "prompt_version": "5",
        "feedback_assistant_id": "asst_J2yNXKyAVxZ9yhxVD1o4roNh",
        "description": "Practice teach-back communication with Mrs. Miller about her heart medication.",
        "icon": "https://i.postimg.cc/FsQTx24r/Mrs-Miller.png",
        "scenario_text": """**Scenario**

It is hospital day four. Ms. Miller's dyspnea has resolved, and she is near her goal weight. You plan to discharge her later this morning.

Your preceptor has asked you to use the teach-back method to ensure Ms. Miller understands her discharge instructions.

**Your Task**

Help Ms. Miller understand:
* Why she was readmitted
* Her medication changes (furosemide 20mg → 40mg daily)
* What to avoid (NSAIDs/over-the-counter pain meds)
* Self-monitoring (daily weights, when to call)

**Remember:** Use plain language and ask open-ended questions like "Can you explain back to me..." rather than "Do you understand?"

Ms. Miller is in her room with her daughter Mary. You may begin when ready.
"""
    },
    "Mr. Aiken (Breaking Bad News)": {
        "display_name": "Mr. Aiken - Breaking Bad News",
        "scenario_type": "Communication Skills",
        "prompt_id": "pmpt_691efa56729c819588300e3506331c5f090acf6790ac551d",
        "prompt_version": "2",
        "feedback_assistant_id": "asst_c7h4U9fu58pgXqGVJkzQyQtr",
        "description": "Practice delivering difficult news with empathy and clarity.",
        "icon": "https://i.postimg.cc/prgb0kPz/Mr-Aiken.png",
        "scenario_text": """**Your Task**

You are about to speak with Mr. Frank Aiken regarding the results of his imaging and current condition. Please address him as you would a real patient: respectfully, clearly, and with empathetic communication. You may ask clarifying questions about his current understanding of his illness, confirm his preferences for how information should be shared, and then deliver the news in a compassionate and supportive manner.

Mr. Aiken may express concerns, ask questions, show emotion, or remain quiet while processing the information. Allow for silence when needed, acknowledge emotions, and avoid technical jargon. Focus on understanding what matters most to him and ensuring that he feels supported during this conversation.

When you are ready, begin by greeting Mr. Aiken and assessing what he understands about his current situation.
"""
    }
}

def get_patient_config(patient_key):
    """Get configuration for a specific patient."""
    return PATIENT_SCENARIOS.get(patient_key)

def get_all_patients():
    """Get list of all available patients."""
    return list(PATIENT_SCENARIOS.keys())