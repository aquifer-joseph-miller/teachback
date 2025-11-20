# patient_config.py

PATIENT_SCENARIOS = {
    "Mrs. Miller (High Value Care 04)": {
        "display_name": "Mrs. Miller - Teach Back",
        "scenario_type": "High Value Care",
        "prompt_id": "pmpt_691cc606dfb4819491acd1328e0488dd0854e783a6e7f3ec",
        "prompt_version": "4",
        "feedback_assistant_id": "asst_J2yNXKyAVxZ9yhxVD1o4roNh",
        "description": "Practice teach-back communication with Mrs. Miller about her heart medication.",
        "icon": "👩‍⚕️"
    },
    "Mr. Aiken (Breaking Bad News)": {
        "display_name": "Mr. Aiken - Breaking Bad News",
        "scenario_type": "Communication Skills",
        "prompt_id": "pmpt_691efa56729c819588300e3506331c5f090acf6790ac551d",
        "prompt_version": "1",
        "feedback_assistant_id": "asst_c7h4U9fu58pgXqGVJkzQyQtr",  
        "description": "Practice delivering difficult news with empathy and clarity.",
        "icon": "👨"
    }
}

def get_patient_config(patient_key):
    """Get configuration for a specific patient."""
    return PATIENT_SCENARIOS.get(patient_key)

def get_all_patients():
    """Get list of all available patients."""
    return list(PATIENT_SCENARIOS.keys())