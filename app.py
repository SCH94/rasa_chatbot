import streamlit as st
from datetime import datetime
from actions.database import DatabaseConnection

db = DatabaseConnection()
st.set_page_config(page_title="Healthcare Triage & Booking", page_icon="🏥", layout="wide")
st.title("🏥 Healthcare Triage and Booking Bot")

if "user_name" not in st.session_state or "user_email" not in st.session_state:
    name = st.text_input("Enter your name:", key="start_name")
    email = st.text_input("Enter your email:", key="start_email")
    if st.button("Continue") and name and email:
        st.session_state.user_name = name.strip()
        st.session_state.user_email = email.strip().lower()
        st.experimental_rerun()
    st.stop()
else:
    name = st.session_state.user_name
    email = st.session_state.user_email

patient = db.get_patient(name, email)
if not patient:
    if st.button("Register and Give GDPR Consent"):
        db.create_or_get_patient(name, email, consent=True)
        st.success("Profile created and consent given!")
        st.experimental_rerun()
    st.stop()

consent = db.check_patient_consent(patient["id"])

if not consent:
    st.warning(
        "🔒 **GDPR Compliance:**\n\n"
        "By using this service, you consent to health data processing for triage/booking. "
        "You can withdraw consent at any time."
    )
    if st.button("✅ I Accept"):
        db.set_patient_consent(patient["id"], True, "GDPR accepted in UI")
        st.success("Consent granted.")
        st.experimental_rerun()
    if st.button("❌ Decline Consent"):
        st.error("You must accept for any chatbot use. Service stopped.")
        db.set_patient_consent(patient["id"], False, "GDPR withdrawn")
        st.stop()
else:
    st.success("✅ GDPR Consent Active")
    if st.button("Withdraw Consent"):
        db.set_patient_consent(patient["id"], False, "GDPR withdrawn")
        st.warning("Consent withdrawn. Data services now disabled.")
        st.stop()

st.markdown("---")
st.subheader(f"👋 Hello **{patient['name']}**!")

msg = st.text_input("Type your question or request...", key="chat_input")
if st.button("Send") and msg and consent:
    st.write("**You:**", msg)
    try:
        import requests
        resp = requests.post(
            "http://localhost:5005/webhooks/rest/webhook",
            json={"sender": f"{name}|{email}", "message": msg},
            timeout=7
        )
        bots = resp.json()
        for b in bots:
            if "text" in b:
                st.info(f"🤖: {b['text']}")
    except Exception:
        st.warning("❗Bot unavailable.")

if consent:
    st.markdown("### 📅 Your Appointments")
    appointments = db.get_patient_appointments(name, email)
    if not appointments:
        st.info("No appointments found.")
    else:
        for a in appointments:
            st.write(f"- **Time:** {a['datetime']}  \n**Doctor:** {a['doctor_name']} ({a['doctor_specialty']})  \n**Status:** {a['status']}")

st.markdown("---")
st.caption("Your health data is protected under GDPR. All actions are auditable.")
