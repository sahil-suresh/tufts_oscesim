import streamlit as st
import threading
import time
from groq import Groq

# --- CONFIGURATION ---
ENCOUNTER_TIME = 600  # 10 minutes

# --- PATIENT SCENARIOS (Keep your SCENARIOS dictionary exactly as it is) ---
SCENARIOS = {
    "Mr. Smith - Leg Ulcer": {
        "name": "James Smith", "age": 72, "gender": "Male",
        "vitals": "BP: 152/90, HR: 74, RR: 20, Temp: 37.2°C, SpO2: 95%, BMI: 29",
        "chief_complaint": "A new blister on his left lower leg.",
        "true_diagnosis": "Venous Stasis Ulcer with co-existing Peripheral Artery Disease (PAD), exacerbated by poorly controlled Diabetes and CHF.",
        "patient_story": """
        - You first noticed the ulcer ten days ago...
        """, # Truncated for brevity, keep your full text
        "physical_exam": {
            "Check Vitals": "Temperature: 37.2°C...",
            # ... and all other physical exam keys
        },
        "lab_results": {
            "Order ABI": "Ankle-Brachial Index (ABI) result is 0.6...",
            # ... and all other lab keys
        },
        "referrals": {
            "Refer to PCP": "Role: Manage the interdisciplinary team...",
            # ... and all other referral keys
        },
        "expert_assessment": {
            # ... Your entire expert_assessment dictionary
        }
    }
    # You can add your other scenarios here as well
}


# --- HELPER FUNCTIONS ---

def initialize_session_state():
    """Sets up the initial state for the Streamlit session."""
    if 'page' not in st.session_state:
        st.session_state.page = 'api_key_entry'
    if 'groq_client' not in st.session_state:
        st.session_state.groq_client = None
    if 'current_scenario_name' not in st.session_state:
        st.session_state.current_scenario_name = None
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'results_log' not in st.session_state:
        st.session_state.results_log = []
    if 'encounter_active' not in st.session_state:
        st.session_state.encounter_active = False
    if 'timer_running' not in st.session_state:
        st.session_state.timer_running = False
    if 'remaining_time' not in st.session_state:
        st.session_state.remaining_time = ENCOUNTER_TIME


def reset_encounter_state():
    """Resets the state for a new encounter."""
    st.session_state.conversation_history = []
    st.session_state.results_log = []
    st.session_state.encounter_active = False
    st.session_state.timer_running = False
    st.session_state.remaining_time = ENCOUNTER_TIME


# --- API AND CHAT LOGIC ---

def call_groq_api(prompt_list):
    """Calls the Groq API and returns the response."""
    try:
        chat_completion = st.session_state.groq_client.chat.completions.create(
            messages=prompt_list,
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=200,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error: Could not connect to Groq API. {e}"


def generate_feedback_from_ai(ddx, plan):
    """Generates feedback using the rubric."""
    scenario = SCENARIOS[st.session_state.current_scenario_name]
    transcript = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.conversation_history[1:]])
    rubric = scenario.get('expert_assessment')
    
    # Using the rubric-based prompt from your desktop app
    ddx_rubric_str = "\n\n".join([f"Diagnosis: {item['diagnosis']}..." for item in rubric['differential_diagnosis_rubric']])
    plan_rubric_str = f"Key Treatment Principles:\n{rubric['management_plan_rubric']['key_treatment_principles']}..."
    
    feedback_prompt = f"""
    You are an expert OSCE examiner...
    --- EXPERT ASSESSMENT RUBRIC (Your Answer Key) ---
    **Expert Differential Diagnosis Analysis:**
    {ddx_rubric_str}
    **Expert Management Plan Analysis:**
    {plan_rubric_str}
    ... (the rest of your detailed feedback prompt) ...
    """
    
    try:
        feedback_completion = st.session_state.groq_client.chat.completions.create(
            messages=[{"role": "user", "content": feedback_prompt}],
            model="llama3-70b-8192",
            temperature=0.5, max_tokens=2048
        )
        return feedback_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating feedback: {e}"


# --- UI RENDERING FUNCTIONS FOR EACH PAGE ---

def render_api_key_page():
    st.header("API Key Required")
    st.write("Please enter your Groq API key to begin the simulation. You can get a free key from [GroqCloud](https://console.groq.com/keys).")
    
    api_key = st.text_input("Groq API Key", type="password", key="api_key_input")

    if st.button("Validate and Continue"):
        if not api_key:
            st.error("API Key cannot be empty.")
        else:
            with st.spinner("Validating API Key..."):
                try:
                    test_client = Groq(api_key=api_key)
                    test_client.chat.completions.create(messages=[{"role": "user", "content": "test"}], model="llama3-8b-8192")
                    st.session_state.groq_client = test_client
                    st.session_state.page = 'scenario_selection'
                    st.success("API Key Validated!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Invalid API Key. Please try again. (Error: {e})")


def render_scenario_selection_page():
    st.title("OSCE Simulator - Select a Scenario")
    for scenario_name in SCENARIOS.keys():
        if st.button(scenario_name, key=scenario_name, use_container_width=True):
            reset_encounter_state()
            st.session_state.current_scenario_name = scenario_name
            st.session_state.page = 'simulation'
            st.rerun()

def render_simulation_page():
    scenario = SCENARIOS[st.session_state.current_scenario_name]
    st.title(f"OSCE Encounter: {scenario['name']}")

    # --- MAIN LAYOUT (3 COLUMNS) ---
    col1, col2, col3 = st.columns([1, 2, 1])

    # --- LEFT COLUMN (Info, Timer, Controls) ---
    with col1:
        st.subheader("Patient Chart")
        st.write(f"**Name:** {scenario['name']}")
        st.write(f"**Age:** {scenario['age']} | **Gender:** {scenario['gender']}")
        st.write("**Vitals:**")
        st.text(scenario['vitals'])
        st.write("**Chief Complaint:**")
        st.info(scenario['chief_complaint'])

        # Timer
        timer_placeholder = st.empty()

        # Start/End Buttons
        if not st.session_state.encounter_active:
            if st.button("▶️ Start Encounter", use_container_width=True):
                st.session_state.encounter_active = True
                st.session_state.timer_running = True
                # Build initial prompt and get patient's greeting
                prompt = f"""
                You are an AI patient simulator... (Your full initial prompt here)
                ---
                Your Patient Story (Base all your answers on this):
                ---
                {scenario['patient_story']}
                ---
                ...
                """
                st.session_state.conversation_history = [{"role": "system", "content": prompt}]
                greeting = call_groq_api(st.session_state.conversation_history)
                st.session_state.conversation_history.append({"role": "assistant", "content": greeting})
                st.rerun()
        else:
            if st.button("⏹️ End Encounter & Assess", use_container_width=True, type="primary"):
                st.session_state.encounter_active = False
                st.session_state.timer_running = False
                st.session_state.page = 'assessment'
                st.rerun()

    # --- CENTER COLUMN (Chat Interface) ---
    with col2:
        st.subheader("Conversation")
        chat_container = st.container(height=500, border=True)
        for msg in st.session_state.conversation_history:
            if msg['role'] != 'system':
                with chat_container.chat_message(name="user" if msg['role'] == 'user' else "assistant"):
                    st.write(msg['content'])

        # User Input
        if st.session_state.encounter_active:
            user_input = st.chat_input("Ask the patient a question...")
            if user_input:
                st.session_state.conversation_history.append({"role": "user", "content": user_input})
                with st.spinner("Patient is thinking..."):
                    response = call_groq_api(st.session_state.conversation_history)
                    st.session_state.conversation_history.append({"role": "assistant", "content": response})
                st.rerun()


    # --- RIGHT COLUMN (Actions and Results) ---
    with col3:
        st.subheader("Clinical Actions")
        
        tab1, tab2, tab3 = st.tabs(["Physical Exam", "Labs/Imaging", "Referrals"])
        
        with tab1:
            for action in scenario['physical_exam'].keys():
                if st.button(action, key=f"exam_{action}", use_container_width=True, disabled=not st.session_state.encounter_active):
                    result = scenario['physical_exam'][action]
                    st.session_state.results_log.append(f"**Physical Exam: {action}**\n\n{result}")
        with tab2:
            for action in scenario['lab_results'].keys():
                if st.button(action, key=f"lab_{action}", use_container_width=True, disabled=not st.session_state.encounter_active):
                    result = scenario['lab_results'][action]
                    st.session_state.results_log.append(f"**Lab/Imaging: {action}**\n\n{result}")
        with tab3:
            for action in scenario['referrals'].keys():
                if st.button(action, key=f"ref_{action}", use_container_width=True, disabled=not st.session_state.encounter_active):
                    result = scenario['referrals'][action]
                    st.session_state.results_log.append(f"**Referral: {action}**\n\n{result}")
        
        st.subheader("Results")
        results_container = st.container(height=300, border=True)
        for res in reversed(st.session_state.results_log):
             results_container.info(res)

    # --- TIMER LOGIC (RUNS AT THE END) ---
    if st.session_state.timer_running:
        while st.session_state.remaining_time > 0:
            mins, secs = divmod(st.session_state.remaining_time, 60)
            timer_placeholder.metric("Timer", f"{mins:02d}:{secs:02d}")
            time.sleep(1)
            st.session_state.remaining_time -= 1
        timer_placeholder.metric("Timer", "Time's Up!")
        st.session_state.encounter_active = False
        st.session_state.timer_running = False
        st.warning("Time's up! Proceeding to assessment.")
        time.sleep(2)
        st.session_state.page = 'assessment'
        st.rerun()
    elif st.session_state.encounter_active:
         mins, secs = divmod(st.session_state.remaining_time, 60)
         timer_placeholder.metric("Timer", f"{mins:02d}:{secs:02d}")

def render_assessment_page():
    st.title("Final Assessment")
    st.info("The encounter has ended. Please provide your differential diagnosis and management plan.")

    ddx = st.text_area("Differential Diagnosis", height=200, placeholder="1. ...\n2. ...\n3. ...")
    plan = st.text_area("Proposed Management Plan", height=200, placeholder="Initial orders, medications, referrals, patient education...")

    if st.button("Submit for Feedback", type="primary"):
        if not ddx or not plan:
            st.error("Please fill out both fields.")
        else:
            with st.spinner("The expert examiner is reviewing your performance..."):
                feedback = generate_feedback_from_ai(ddx, plan)
                st.session_state.feedback = feedback
                st.session_state.page = 'feedback'
                st.rerun()

def render_feedback_page():
    st.title("OSCE Performance Feedback")
    st.markdown(st.session_state.feedback)

    if st.button("↩️ Return to Scenario Selection"):
        st.session_state.page = 'scenario_selection'
        # Do not reset the Groq client
        st.rerun()

# --- MAIN APP ROUTER ---
st.set_page_config(layout="wide", page_title="OSCE Patient Simulator")

initialize_session_state()

if st.session_state.page == 'api_key_entry':
    render_api_key_page()
elif st.session_state.page == 'scenario_selection':
    render_scenario_selection_page()
elif st.session_state.page == 'simulation':
    render_simulation_page()
elif st.session_state.page == 'assessment':
    render_assessment_page()
elif st.session_state.page == 'feedback':
    render_feedback_page()