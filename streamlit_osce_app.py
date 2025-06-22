import streamlit as st
import time
from groq import Groq

# --- CONFIGURATION ---
# (Same as original)
ENCOUNTER_TIME = 600  # 10 minutes

# --- PATIENT SCENARIOS ---
# (Same as original, truncated for brevity in this comment block but full in code)
SCENARIOS = {
    "Mr. Smith - Leg Ulcer": {
        "name": "James Smith", "age": 72, "gender": "Male",
        "vitals": "BP: 152/90, HR: 74, RR: 20, Temp: 37.2°C, SpO2: 95%, BMI: 29",
        "chief_complaint": "A new blister on his left lower leg.",
        "true_diagnosis": "Venous Stasis Ulcer with co-existing Peripheral Artery Disease (PAD), exacerbated by poorly controlled Diabetes and CHF.",
        "patient_story": """
        - You first noticed the ulcer ten days ago.
        - It seemed to get larger, and 3 days ago started to release a thin bloody fluid.
        - You've never had these kinds of blisters before, but your skin seems thin and gets damaged easily if you bump your leg.
        - Your everyday shoes feel tighter than usual.
        - You deny having fevers or chills, but the ulcer site feels warm and is tender to the touch.
        - At first you did nothing, but once it started draining, you started cleaning it with soap and water and covering it with gauze.
        - You've also noticed pain in your legs that is worse when you walk (claudication), especially up and down stairs, but it gets better when you rest.
        - You deny any numbness or tingling in your feet.
        - You've been feeling more short of breath lately with activity.
        - Your medical history includes: Coronary Artery Disease (had a CABG surgery at age 67), Aortic Stenosis, and Congestive Heart Failure.
        - You also have Type 2 Diabetes, diagnosed in your 50s.
        - Your mother died of a stroke at 72 (she also had diabetes). Your father died of a heart attack at 70 (he had high cholesterol).
        - You are a retired accountant and a current smoker with a 50-pack-year history. You drink 1-2 beers a week.
        - You live in a two-story home with your wife, who had a stroke 2 years ago. Your bedroom is on the second floor.
        - REGARDING YOUR MEDICATIONS:
        - You recently stopped taking your Lisinopril because you noticed it gives you an annoying cough.
        - You know Furosemide is a 'water pill' so you often skip it on days you plan to go out, so you don't have to be near a bathroom.
        - You take your Atorvastatin, Aspirin, Metoprolol, and Dapagliflozin as prescribed.
        """,
        "physical_exam": {
            "Check Vitals": "Temperature: 37.2°C, Blood Pressure: 152/90, HR: 74 bpm, RR: 20, SpO2: 95% on room air, BMI: 29.",
            "Auscultate Heart": "Crescendo-decrescendo systolic murmur heard best at the upper right sternal border, radiating to the carotids. An S3 gallop is present. Rhythm is regular.",
            "Auscultate Chest": "Bibasilar crackles are heard on auscultation. No wheezes.",
            "Check JVP": "Jugular Venous Pressure (JVP) is elevated at 10 cm.",
            "Inspect Extremities": "Upon removing socks/shoes: Bilateral 2+ pitting edema is present up to the mid-thigh. Scars from bilateral saphenous vein harvesting are visible. Toes are encrusted with severely dystrophic toenails.",
            "Examine Lower Leg Ulcer": "A 5cm x 5.5cm ulcer is located on the anterior calf. The border is round and irregular. The base is red, moist, and granulating. There is a moderate amount of serosanguinous drainage. The periwound skin shows scaling and hemosiderin deposition. There is no crepitus, fluctuance, or malodor.",
            "Check Peripheral Pulses": "Pedal pulses (dorsalis pedis, posterior tibialis) are non-palpable bilaterally. Doppler signals are monophasic.",
            "Check Capillary Refill": "Capillary refill in the toes is delayed, >3 seconds.",
            "Perform Monofilament Test": "Patient has loss of protective sensation in a stocking distribution on both feet when tested with a 10g monofilament.",
            "Assess Gait": "Patient walks with slow, small steps. Gait is flat-footed with limited knee flexion and extension, likely due to significant edema and pain.",
            "Palpate Abdomen": "Abdomen is soft, non-tender, non-distended. No hepatosplenomegaly.",
            "Neurological Exam": "Cranial nerves II-XII are intact. Strength is 5/5 throughout. Sensation to light touch is decreased in lower extremities."
        },
        "lab_results": {
            "Order ABI": "Ankle-Brachial Index (ABI) result is 0.6, consistent with moderate peripheral artery disease.",
            "Order Arterial Duplex": "Ultrasound shows monophasic waveforms throughout the lower extremities, confirming significant PAD.",
            "Order Venous Duplex": "Ultrasound shows no acute DVT. There is evidence of great saphenous and perforator vein reflux, consistent with chronic venous insufficiency.",
            "Order Wound Culture Swab": "Culture results are pending. Gram stain shows mixed flora with both gram-positive cocci and gram-negative rods.",
            "Order ESR/CRP": "ESR: 45 mm/hr (Elevated), CRP: 2.5 mg/dL (Elevated).",
            "Order CBC": "WBC: 7.2 (Normal), Hgb: 11.6 (Mild Anemia), Hct: 35%, Platelets: 320,000.",
            "Order BMP": "Na+: 135, K+: 4.0, Cl-:100, Bicarbonate: 24, BUN: 28 (Elevated), Cr: 1.4 (Elevated).",
            "Order HbA1c": "HbA1c is 8.5% (Poorly controlled).",
            "Order ECG": "Shows normal sinus rhythm with non-specific ST changes. No signs of acute ischemia. The tracing is stable compared to a previous ECG from 3 months ago.",
            "Order Chest X-Ray": "CXR reveals mild cardiomegaly and bibasilar atelectasis/edema, consistent with a mild CHF exacerbation.",
            "Order Troponin": "Troponin is <0.01 ng/mL (Negative)."
        },
        "referrals": {
            "Refer to PCP": "Role: Manage the interdisciplinary team, monitor progress, order labs, coordinate care, manage smoking cessation, and evaluate nutrition.",
            "Refer to Cardiologist": "Role: Manage the patient's Peripheral Artery Disease (PAD), claudication, and Congestive Heart Failure (CHF), including diuresis. Will assess for medical management vs. revascularization of lower extremities.",
            "Refer to Podiatrist": "**Emergency Consult Recommended**\nRole: Management of complex toe/toenail pathology, provide education on daily foot checks, perform regular foot exams, and assess footwear/hygiene for risk reduction.",
            "Refer to Wound Care": "Role: Provide expert wound management including debridement, moist wound care, and edema control (compression therapy). Will coordinate with vascular surgery if needed.",
            "Refer to Social Work": "Role: Arrange home health care, assess for mobility barriers at home (e.g., stairs), and connect the patient/family to programs and insurance coverage resources.",
            "Refer to Home Health": "Role: A Home Health Aide (HHA) can be arranged for regular dressing changes and medication compliance checks.",
            "Refer to Physical Therapy": "Role: Address mobility issues resulting from claudication pain and severe edema. Can provide an exercise regimen and gait training."
        },
        "expert_assessment": {
            "differential_diagnosis_rubric": [
                {
                    "diagnosis": "Mixed Arterial-Venous Leg Ulcer",
                    "concordant_features": "Edema, Venous duplex reflux, Claudication symptoms (ABI=0.6), CHF, Monophasic doppler, Posterior calf location, Granulating base, Serosanguinous drainage, Dystrophic toenails (ischemia).",
                    "discordant_features": "Non-classical location (not medial 'gaiter' region).",
                    "absent_but_expected_features": "N/A"
                },
                {
                    "diagnosis": "Arterial Insufficiency Ulcer",
                    "concordant_features": "Monophasic Doppler, Nonpalpable pulses, Claudication symptoms, ABI=0.6, CAD history, Smoking history, Dystrophic toenails (ischemia), Delayed capillary refill.",
                    "discordant_features": "Significant serosanguinous drainage and edema (more typical of venous), Not a 'punched out' appearance, Not dry, Location is posterior calf rather than toes/heel.",
                    "absent_but_expected_features": "N/A"
                },
                {
                    "diagnosis": "Venous Stasis Ulcer",
                    "concordant_features": "Venous duplex reflux, Significant edema, Hemosiderin staining, CHF history, Red granulating base, Scaling periwound (stasis dermatitis), Bibasilar crackles.",
                    "discordant_features": "ABI=0.6 (indicates significant arterial component), Dystrophic toenails (ischemia), Claudication symptoms.",
                    "absent_but_expected_features": "No lipodermatosclerosis, Abnormal location (not medial calf)."
                },
                {
                    "diagnosis": "Diabetic (Neuropathic) Ulcer",
                    "concordant_features": "Poorly controlled diabetes (A1c 8.5%), Co-existing vascular disease, Dystrophic toenails.",
                    "discordant_features": "Protective sensation was lost on monofilament test, but ulcers are typically painless. Location is not on a typical weight-bearing surface (like bottom of foot). Ulcer is not necrotic.",
                    "absent_but_expected_features": "Typically found on weight-bearing surfaces."
                }
            ],
            "management_plan_rubric": {
                "key_treatment_principles": """
- **Initial Management:** Recognition that the ulcer is too tender for immediate sharp debridement.
- **First-Line Therapy:** Autolytic debridement (using moisture-retentive dressings) combined with **modified/reduced compression therapy**. Standard high compression is contraindicated due to the arterial disease (ABI=0.6).
- **Pathophysiology:** Understanding the interplay of venous hypertension (causing edema and leakage) and arterial insufficiency (causing ischemia and poor healing).
""",
                "goals_of_care": """
- Pain and odor control.
- Rapid return to prior functional status.
- **Preventing recurrence** through long-term management.
""",
                "plan_of_care_considerations": """
- **Patient Capabilities:** Recognize the need for Home Health due to complex medical needs and potential difficulty with self-care.
- **Adherence:** Acknowledge patient's prior non-adherence (Lisinopril, Furosemide) and incorporate medication counseling and simplification.
- **Family/Social Support:** Involve family in care instructions and assess their ability to help with appointments and home care.
- **Interdisciplinary Team:** The plan must involve referrals to specialists (Cardiology, Podiatry, Wound Care) and support services (Social Work, PT, Home Health).
- **Cost:** Acknowledge the need to understand insurance coverage for referrals and supplies.
"""
            }
        }
    }
}

# --- HELPER FUNCTIONS ---

def initialize_state():
    """Initializes the session state variables."""
    if "page" not in st.session_state:
        st.session_state.page = "api_key_entry"
    if "groq_client" not in st.session_state:
        st.session_state.groq_client = None
    if "current_scenario" not in st.session_state:
        st.session_state.current_scenario = None
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    if "results" not in st.session_state:
        st.session_state.results = []
    if "encounter_active" not in st.session_state:
        st.session_state.encounter_active = False
    if "start_time" not in st.session_state:
        st.session_state.start_time = 0
    if "feedback" not in st.session_state:
        st.session_state.feedback = ""

def call_groq_api():
    """Calls the Groq API and updates the conversation history."""
    try:
        chat_completion = st.session_state.groq_client.chat.completions.create(
            messages=st.session_state.conversation_history,
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=200,
        )
        response = chat_completion.choices[0].message.content
        st.session_state.conversation_history.append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"Error communicating with Groq API: {e}")
        # Add an error message to history to unblock user
        st.session_state.conversation_history.append({"role": "assistant", "content": f"Sorry, a system error occurred: {e}"})

def build_initial_prompt():
    """Creates the initial system prompt for the Groq AI."""
    scenario = st.session_state.current_scenario
    prompt = f"""
    You are an AI patient simulator for a medical OSCE.
    Your name is {scenario['name']}, you are a {scenario['age']}-year-old {scenario['gender']}.
    Your chief complaint is: "{scenario['chief_complaint']}".

    You MUST follow these rules:
    1.  Act exactly like the patient based on the history provided below. Respond naturally, in the first person. Do not act like an AI.
    2.  Do NOT reveal any information from your 'Patient Story' unless the user asks a specific and relevant question.
    3.  Keep your answers concise and patient-like. Express emotion like pain or anxiety where appropriate.
    4.  If you don't have information about a specific question, say something like 'I don't know' or 'I'm not sure, doctor.'
    5.  Do NOT respond to or acknowledge physical exam or lab orders. The system handles those separately. Only answer conversational questions.

    Your Patient Story (Base all your answers on this):
    ---
    {scenario['patient_story']}
    ---
    The user is a physician-in-training. The encounter now begins. Your first response should be a simple greeting.
    """
    st.session_state.conversation_history = [{"role": "system", "content": prompt}]
    # Get the initial greeting from the patient
    call_groq_api()

def perform_action(action_key):
    """Handles a physical exam, lab order, or referral."""
    scenario = st.session_state.current_scenario
    result_type = "Action"
    result = None

    if action_key in scenario.get('physical_exam', {}):
        result = scenario['physical_exam'][action_key]
        result_type = "Physical Exam"
    elif action_key in scenario.get('lab_results', {}):
        result = scenario['lab_results'][action_key]
        result_type = "Lab/Imaging"
    elif action_key in scenario.get('referrals', {}):
        result = scenario['referrals'][action_key]
        result_type = "Referral"

    if result:
        result_text = f"**{result_type} Result for '{action_key}':**\n\n{result}"
        st.session_state.results.append(result_text)
        st.session_state.conversation_history.append(
            {"role": "system", "content": f"'{action_key}' was performed. See the 'Results' tab for findings."}
        )
    else:
        st.session_state.conversation_history.append(
            {"role": "system", "content": f"The action '{action_key}' is not relevant or available for this patient scenario."}
        )

# --- PAGE RENDERING FUNCTIONS ---

def render_api_key_entry():
    """Displays the screen for entering the Groq API key."""
    st.header("Modern OSCE Patient Simulator")
    st.subheader("API Key Required")

    st.markdown("Please enter your Groq API key to begin the simulation. Your key is not stored or shared.")
    
    api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_...")

    if st.button("Validate and Continue"):
        if not api_key:
            st.error("API Key cannot be empty.")
            return

        with st.spinner("Validating API key..."):
            try:
                test_client = Groq(api_key=api_key)
                test_client.chat.completions.create(messages=[{"role": "user", "content": "test"}], model="llama3-8b-8192")
                st.session_state.groq_client = test_client
                st.session_state.page = "scenario_selection"
                st.rerun()
            except Exception as e:
                st.error(f"Invalid API Key. Please try again. Error: {e}")

# CORRECTED VERSION

def render_scenario_selection():
    """Displays the screen to select a patient scenario."""
    st.header("Select a Patient Scenario")
    
    for scenario_name in SCENARIOS.keys():
        # The 'height=50' parameter has been removed from this line
        if st.button(scenario_name, use_container_width=True):
            # Reset state for a new encounter
            st.session_state.current_scenario = SCENARIOS[scenario_name]
            st.session_state.conversation_history = []
            st.session_state.results = []
            st.session_state.encounter_active = False
            st.session_state.start_time = 0
            st.session_state.feedback = ""
            st.session_state.page = "main_encounter"
            st.rerun()

def render_main_encounter():
    """Renders the main UI for the OSCE simulation."""
    scenario = st.session_state.current_scenario
    st.title(f"OSCE Encounter: {scenario['name']}")

    # --- Layout ---
    left_col, center_col, right_col = st.columns([1, 2, 1])

    # --- Left Panel (Patient Info & Controls) ---
    with left_col:
        st.header("Patient Chart")
        
        # Timer
        timer_placeholder = st.empty()

        info_text = f"""
        - **Name:** {scenario['name']}
        - **Age:** {scenario['age']}
        - **Gender:** {scenario['gender']}
        
        **Vitals:**
        {scenario['vitals']}
        
        **Chief Complaint:**
        {scenario['chief_complaint']}
        """
        st.markdown(info_text)

        if not st.session_state.encounter_active:
            if st.button("Start Encounter", type="primary", use_container_width=True):
                st.session_state.encounter_active = True
                st.session_state.start_time = time.time()
                build_initial_prompt()
                st.rerun()
        
        if st.session_state.encounter_active:
            if st.button("End Encounter & Assess", type="secondary", use_container_width=True):
                st.session_state.encounter_active = False
                st.session_state.page = "assessment"
                st.rerun()

    # --- Center Panel (Conversation) ---
    with center_col:
        st.header("Conversation")
        chat_container = st.container(height=600, border=True)

        for message in st.session_state.conversation_history:
            if message["role"] == "system":
                # Don't show the initial system prompt, but show system messages
                if not message["content"].startswith("You are an AI patient simulator"):
                    chat_container.info(message["content"])
            else:
                with chat_container.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Handle chat input
        if prompt := st.chat_input("Type your question to the patient...", disabled=not st.session_state.encounter_active):
            st.session_state.conversation_history.append({"role": "user", "content": prompt})
            with chat_container.chat_message("user"):
                st.markdown(prompt)
            
            with st.spinner("Patient is thinking..."):
                call_groq_api()
            st.rerun()

    # --- Right Panel (Actions & Results) ---
    with right_col:
        st.header("Actions & Results")
        
        exam_tab, labs_tab, referrals_tab, results_tab = st.tabs(["Physical Exam", "Order Labs/Imaging", "Referrals", "Results"])

        with exam_tab:
            exam_actions = list(scenario.get('physical_exam', {}).keys())
            for action in exam_actions:
                if st.button(action, key=f"exam_{action}", use_container_width=True, disabled=not st.session_state.encounter_active):
                    perform_action(action)
                    st.rerun()

        with labs_tab:
            lab_actions = list(scenario.get('lab_results', {}).keys())
            for action in lab_actions:
                if st.button(action, key=f"lab_{action}", use_container_width=True, disabled=not st.session_state.encounter_active):
                    perform_action(action)
                    st.rerun()
        
        with referrals_tab:
            referral_actions = list(scenario.get('referrals', {}).keys())
            for action in referral_actions:
                if st.button(action, key=f"ref_{action}", use_container_width=True, disabled=not st.session_state.encounter_active):
                    perform_action(action)
                    st.rerun()

        with results_tab:
            if not st.session_state.results:
                st.info("Results from exams, labs, and referrals will appear here.")
            else:
                for res in reversed(st.session_state.results):
                    st.markdown("---")
                    st.markdown(res)
    
    # --- Timer Logic ---
    if st.session_state.encounter_active:
        elapsed_time = time.time() - st.session_state.start_time
        remaining_time = ENCOUNTER_TIME - elapsed_time
        
        if remaining_time > 0:
            mins, secs = divmod(int(remaining_time), 60)
            timer_placeholder.metric("Timer", f"{mins:02d}:{secs:02d}")
        else:
            timer_placeholder.metric("Timer", "Time's Up!", delta="-10:00", delta_color="inverse")
            st.session_state.encounter_active = False
            # Automatically move to assessment when time is up
            st.toast("Time's up! Please complete your assessment.")
            time.sleep(2) # Give user a moment to see the message
            st.session_state.page = "assessment"
            st.rerun()

def render_assessment():
    """Renders the final assessment form."""
    st.title("Final Assessment")
    st.markdown("The encounter has ended. Please provide your differential diagnosis and proposed management plan.")

    with st.form("assessment_form"):
        ddx = st.text_area(
            "**Differential Diagnosis**",
            height=200,
            placeholder="List your differential diagnoses, starting with the most likely."
        )
        plan = st.text_area(
            "**Proposed Management Plan**",
            height=200,
            placeholder="Outline your plan for investigations, treatment, and patient education."
        )
        
        submitted = st.form_submit_button("Submit for Feedback")

        if submitted:
            if not ddx or not plan:
                st.error("Please fill out both fields before submitting.")
            else:
                with st.spinner("Generating expert feedback on your performance... This may take a moment."):
                    generate_feedback(ddx, plan)
                st.session_state.page = "feedback"
                st.rerun()

def generate_feedback(ddx, plan):
    """Asks the AI to generate feedback on the user's performance."""
    scenario = st.session_state.current_scenario
    transcript = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.conversation_history if msg['role'] != 'system'])
    
    feedback_prompt = ""

    # Use the detailed rubric-based prompt if available
    if 'expert_assessment' in scenario:
        rubric = scenario['expert_assessment']
        ddx_rubric_str = "\n\n".join([
            f"Diagnosis: {item['diagnosis']}\n- Concordant: {item['concordant_features']}\n- Discordant: {item['discordant_features']}"
            for item in rubric['differential_diagnosis_rubric']
        ])
        plan_rubric_str = (
            f"Key Treatment Principles:\n{rubric['management_plan_rubric']['key_treatment_principles']}\n\n"
            f"Goals of Care:\n{rubric['management_plan_rubric']['goals_of_care']}\n\n"
            f"Plan of Care Considerations:\n{rubric['management_plan_rubric']['plan_of_care_considerations']}"
        )
        feedback_prompt = f"""
        You are an expert OSCE examiner providing objective, standardized feedback based on a provided rubric.
        A medical student has completed an encounter.
        - **Patient's True Diagnosis:** {scenario['true_diagnosis']}
        - **Full Encounter Transcript:** \n{transcript}
        --- STUDENT'S SUBMISSION ---
        **Student's Differential Diagnosis:**
        {ddx}
        **Student's Management Plan:**
        {plan}
        ---
        --- EXPERT ASSESSMENT RUBRIC (Your Answer Key) ---
        **Expert Differential Diagnosis Analysis:**
        {ddx_rubric_str}
        **Expert Management Plan Analysis:**
        {plan_rubric_str}
        ---
        **YOUR TASK:**
        Provide structured, constructive feedback in markdown format by **strictly comparing the student's submission to the Expert Assessment Rubric**. Do not invent new criteria.
        1.  **Differential Diagnosis Evaluation:**
            -   Compare the student's DDx list to the expert rubric. Did they identify the most likely diagnoses?
            -   Assess their reasoning. Did they cite the correct features from the case, as outlined in the rubric?
        2.  **Management Plan Evaluation:**
            -   Does the student's plan align with the 'Key Treatment Principles' (e.g., modified compression)?
            -   Did it address the 'Goals of Care' and 'Plan of Care Considerations' (e.g., non-adherence, referrals)?
        3.  **History Taking & Physical Exam Performance:**
            -   Briefly comment on the student's interaction. Did they ask key questions (e.g., claudication, medication adherence)? Did they perform key exams (e.g., pulses, JVP)?
        4.  **Overall Summary & Key Learning Points:**
            -   Provide a final summary of what was done well and the most important learning points.
        """
    else: # Fallback prompt if no rubric exists
        feedback_prompt = f"""
        You are an expert OSCE examiner reviewing a medical student's performance.
        The student has just completed an encounter with a simulated patient.
        PATIENT'S TRUE DIAGNOSIS: {scenario['true_diagnosis']}
        Here is the full transcript of the encounter:
        --- TRANSCRIPT START ---
        {transcript}
        --- TRANSCRIPT END ---
        After the encounter, the student provided the following assessment:
        --- STUDENT'S DIFFERENTIAL DIAGNOSIS ---
        {ddx}
        --- STUDENT'S MANAGEMENT PLAN ---
        {plan}
        ---
        Your task is to provide structured, constructive feedback in markdown format on:
        1. History Taking, 2. Physical Exam & Investigations, 3. Differential Diagnosis, 4. Management Plan, 5. Overall Summary & Key Learning Points.
        """
    
    try:
        feedback_completion = st.session_state.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": feedback_prompt}],
            model="llama3-70b-8192", # Larger model for better analysis
            temperature=0.5,
            max_tokens=2048,
        )
        st.session_state.feedback = feedback_completion.choices[0].message.content
    except Exception as e:
        st.session_state.feedback = f"Error generating feedback: {e}"

def render_feedback():
    """Displays the final feedback."""
    st.title("OSCE Performance Feedback")
    st.markdown(st.session_state.feedback)
    
    if st.button("Return to Scenario Selection", use_container_width=True):
        st.session_state.page = "scenario_selection"
        # Clear specific encounter data but keep the client
        st.session_state.current_scenario = None
        st.session_state.conversation_history = []
        st.session_state.results = []
        st.session_state.encounter_active = False
        st.session_state.start_time = 0
        st.session_state.feedback = ""
        st.rerun()

# --- MAIN APP LOGIC ---

# Set page config for wide mode
st.set_page_config(layout="wide", page_title="Modern OSCE Simulator")

# Initialize state on first run
initialize_state()

# Page router
if st.session_state.page == "api_key_entry":
    render_api_key_entry()
elif st.session_state.page == "scenario_selection":
    render_scenario_selection()
elif st.session_state.page == "main_encounter":
    render_main_encounter()
elif st.session_state.page == "assessment":
    render_assessment()
elif st.session_state.page == "feedback":
    render_feedback()