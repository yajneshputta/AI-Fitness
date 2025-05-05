# ✅ Fully Integrated Enhanced Fitness Assistant App

import streamlit as st
import json
import os
import requests
from fpdf import FPDF
import fitz  # PyMuPDF
import plotly.graph_objects as go
import plotly.io as pio
import time

# -------- CONFIG --------
# Load Groq API key from Streamlit secrets
if "GROQ_API_KEY" in st.secrets:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
else:
    st.error("Missing GROQ_API_KEY in .streamlit/secrets.toml")
    st.stop()

GROQ_MODEL = "llama3-70b-8192"
DATA_FILE = "user_data.json"
RESPONSES_FILE = "agent_responses.json"

# Initialize session state
st.session_state.setdefault("latest_plan", "")
st.session_state.setdefault("theme_mode", "light")
st.session_state.setdefault("agent_responses", {})

# -------- UTILS --------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"personal": {}, "goals": [], "nutrition": {}, "notes": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def call_groq(prompt):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    body = {"messages": [{"role": "user", "content": prompt}], "model": GROQ_MODEL}
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
    if res.status_code != 200:
        st.error(f"Groq API Error: {res.status_code} - {res.text}")
        return "❌ Groq API error."
    try:
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"Error parsing Groq response: {e}")
        return "❌ Failed to parse Groq response."

# add code to get human feedback
def update_feedback(orig_prompt, feedback_label):
    txt = st.text_input(
        label = feedback_label,
        max_chars = 200)
    if st.button ("Submit") and txt:
       # st.write ("Updating your plan...")        
        prompt = orig_prompt + txt
        print (prompt)
        newplan = call_groq(prompt)
        print (newplan)
        st.rerun()
    return
def export_pdf_from_text(title, text_dict):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=1, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    for key, val in text_dict.items():
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, key, ln=1)
        pdf.set_font("Arial", size=12)
        for line in str(val).split("\n"):
            pdf.multi_cell(0, 8, line)
        pdf.ln(3)
    return pdf.output(dest="S").encode('latin-1')

def extract_pdf_text(uploaded):
    with fitz.open(stream=uploaded.read(), filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)

# -------- PAGE CONFIG --------
st.set_page_config(page_title="AI Fitness Assistant", layout="wide")

# -------- SIDEBAR --------
st.sidebar.title("⚙️ Settings")
if st.sidebar.button("🔄 Reset All Data"):
    if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
    if os.path.exists(RESPONSES_FILE): os.remove(RESPONSES_FILE)
    for k in ["latest_plan","agent_responses"]:
        st.session_state.pop(k, None)
    st.success("Data reset. Please refresh the page.")
    st.stop()

mode = st.sidebar.selectbox("Theme", ["Light","Dark"],
                            index=0 if st.session_state.theme_mode=="light" else 1)
st.session_state.theme_mode = mode.lower()
if st.session_state.theme_mode == "dark":
    st.markdown("""
        <style>
            body, .stApp { background-color: #0e1117; color: white; }
            .stTextInput input, .stTextArea textarea, .stNumberInput input { background: #1a1a1a; color: white; }
            .stButton button { background: #333; color: white; border: 1px solid #888; }
        </style>
    """, unsafe_allow_html=True)
    pio.templates.default = "plotly_dark"
else:
    pio.templates.default = "plotly"
    st.markdown("""
    <style>
        body, .stApp {
            background-color: #f9f9f9;
            color: #333333;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        }
        .css-1d391kg, .css-12w0qpk {
            background-color: #ffffff !important;
            border-radius: 10px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
            padding: 1rem !important;
            margin-bottom: 1rem !important;
        }
        .stButton>button {
            background-color: #007bff !important;
            color: white !important;
            border: none !important;
            border-radius: 5px !important;
            padding: 0.5rem 1rem !important;
        }
        .stButton>button:hover {
            background-color: #0069d9 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# -------- LOAD DATA --------
data = load_data()

# -------- HEADER --------
st.title("🏋️ AI Fitness Assistant")
st.write("Groq-powered • Personalized • Interactive")

# -------- PERSONAL INFO --------
st.markdown("---")
st.subheader("👤 Personal Information")
with st.form("profile_form"):
    name   = st.text_input("Name",  data["personal"].get("name",""))
    age    = st.number_input("Age",  min_value=0,  max_value=120, value=data["personal"].get("age",0))
    weight = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0, value=data["personal"].get("weight",0.0))
    height = st.number_input("Height (cm)", min_value=0.0, max_value=250.0, value=data["personal"].get("height",0.0))
    gender = st.selectbox("Gender", ["Male","Female","Other"], index=0)
    if st.form_submit_button("Save Profile"):
        data["personal"] = {"name":name,"age":age,"weight":weight,"height":height,"gender":gender}
        save_data(data); st.success("Profile saved!")

# -------- GOALS --------
st.markdown("---")
st.subheader("🎯 Fitness Goals")
goals = st.multiselect("Goals", ["Muscle Gain","Weight Loss","Endurance","Rehab"], data.get("goals",[]))
if st.button("Save Goals"):
    data["goals"] = goals; save_data(data); st.success("Goals saved!")

# -------- NUTRITION --------
st.markdown("---")
st.subheader("🍎 Nutrition Targets")
calories = st.number_input("Calories", value=data.get("nutrition",{}).get("calories",2000))
protein  = st.number_input("Protein (g)", value=data.get("nutrition",{}).get("protein",100))
fat      = st.number_input("Fat (g)", value=data.get("nutrition",{}).get("fat",70))
carbs    = st.number_input("Carbs (g)", value=data.get("nutrition",{}).get("carbs",250))
col1,col2= st.columns(2)
with col1:
    if st.button("Save Nutrition"):
        data["nutrition"] = {"calories":calories,"protein":protein,"fat":fat,"carbs":carbs}
        save_data(data); st.success("Nutrition saved!")
with col2:
    if st.button("AI Nutrition Plan"):
        prompt = f"Generate meal plan for a {age}-year-old {gender} {weight}kg aiming {', '.join(goals)}."
        plan = call_groq(prompt)
        st.info(plan)
        feedback_label = "If you would like to make any changes to your nutritional plan, please enter below"
        update_feedback(prompt, feedback_label)

# -------- MACRO CHART --------
if data.get("nutrition"):
    st.markdown("---")
    st.subheader("📊 Macro Breakdown")
    m = data["nutrition"]
    fig = go.Figure(go.Bar(
        x=[m["protein"],m["fat"],m["carbs"]],
        y=["Protein","Fat","Carbs"],
        orientation='h'
    ))
    fig.update_layout(template=pio.templates.default, height=300)
    st.plotly_chart(fig, use_container_width=True)

# -------- NOTES --------
st.markdown("---")
st.subheader("📝 Special Notes")
for i,note in enumerate(data["notes"]):
    cols = st.columns([4,1,1])
    new_note = cols[0].text_input("", note, key=f"note_{i}")
    if cols[1].button("💾 Save", key=f"save_{i}"):
        data["notes"][i] = new_note; save_data(data); st.rerun()
    if cols[2].button("❌ Delete", key=f"del_{i}"):
        data["notes"].pop(i); save_data(data); st.rerun()
new_note = st.text_input("Add a new note")
if st.button("Add Note") and new_note:
    data["notes"].append(new_note); save_data(data); st.rerun()

# -------- PDF UPLOAD --------
st.markdown("---")
st.subheader("📤 Upload Workout Plan (PDF)")
uploaded_file = st.file_uploader("Drop your PDF here", type="pdf")
if uploaded_file:
    pdf_text = extract_pdf_text(uploaded_file)
    st.text_area("Extracted Text", pdf_text, height=200)

# -------- MULTI-AGENT --------
st.markdown("---")
st.subheader("🧠 Multi-Agent Assistant")
tabs = st.tabs(["🏋️ Workout Planner","🥗 Nutritionist","🦵 Rehab Advisor","🧮 Fitness Calculator"])

with tabs[0]:
    query = st.text_input("👟 Workout Question", key="mq1")
    if st.button("Ask Workout Planner", key="b1") and query.strip():
        with st.spinner("Planning your workout..."):
            prompt = (
                f"Design a personalized workout plan for the following user:\n"
                f"Profile: {data['personal']}\n"
                f"Goals: {', '.join(goals)}\n"
                f"Notes: {'; '.join(data['notes'])}\n"
                f"Question: {query}"
            )
            response = call_groq(prompt)
            st.session_state.agent_responses['Workout Planner'] = response
            st.markdown("#### 💡 Response:")
            st.success(response)

with tabs[1]:
    query = st.text_input("🥗 Nutrition Question", key="mq2")
    if st.button("Ask Nutritionist", key="b2") and query.strip():
        with st.spinner("Consulting nutritionist..."):
            prompt = (
                f"You are a certified fitness nutritionist.\n"
                f"Profile: {data['personal']}\nGoals: {', '.join(goals)}\nNotes: {'; '.join(data['notes'])}\n"
                f"Question: {query}"
            )
            response = call_groq(prompt)
            st.session_state.agent_responses['Nutritionist'] = response
            st.markdown("#### 💡 Response:")
            st.info(response)

with tabs[2]:
    query = st.text_input("🦵 Rehab Question", key="mq3")
    if st.button("Ask Rehab Advisor", key="b3") and query.strip():
        with st.spinner("Consulting rehab advisor..."):
            prompt = (
                f"You are a certified rehab specialist.\n"
                f"Profile: {data['personal']}\nInjury Notes: {'; '.join(data['notes'])}\n"
                f"Question: {query}"
            )
            response = call_groq(prompt)
            st.session_state.agent_responses['Rehab Advisor'] = response
            st.markdown("#### ⚠️ Caution:")
            st.warning(response)

with tabs[3]:
    query = st.text_input("🧮 Calculation Question", key="mq4")
    if st.button("Ask Fitness Calculator", key="b4") and query.strip():
        with st.spinner("Crunching numbers..."):
            prompt = f"You are a fitness calculator assistant. Question: {query}"
            response = call_groq(prompt)
            st.session_state.agent_responses['Fitness Calculator'] = response
            st.markdown("#### 🧮 Result:")
            st.success(response)

# -------- DOWNLOAD RESPONSES --------
st.markdown("---")
st.subheader("📄 Download All Agent Responses")
if st.session_state.agent_responses:
    pdf_bytes = export_pdf_from_text("AI Fitness Assistant Responses", st.session_state.agent_responses)
    st.download_button("📥 Download Responses as PDF", data=pdf_bytes, file_name="fitness_agent_responses.pdf", mime="application/pdf")
