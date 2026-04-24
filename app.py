import streamlit as st
from dotenv import load_dotenv
import os
import google.generativeai as genai
import requests
from urllib.parse import urlparse, parse_qs

# Load environment variables
load_dotenv()

# Custom CSS
css = """
body {
  background: #f6f8fa;
}
.st-emotion-cache-1v0mbdj {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.07);
  padding: 2rem;
}
.hero-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2d3748;
  margin-bottom: 0.5rem;
}
.hero-sub {
  font-size: 1.2rem;
  color: #4a5568;
  margin-bottom: 2rem;
}
.result-card {
  background: #e6fffa;
  border-radius: 12px;
  padding: 1.5rem;
  margin-top: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.hospital-card {
  background: #f7fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}
.emergency {
  color: #e53e3e;
  font-weight: bold;
}
.urgent {
  color: #d69e2e;
  font-weight: bold;
}
.normal {
  color: #38a169;
  font-weight: bold;
}
.disclaimer {
  font-size: 0.95rem;
  color: #718096;
  margin-top: 2rem;
  text-align: center;
}
.stButton>button {
  border-radius: 8px;
  font-weight: 600;
  padding: 0.6rem 1.2rem;
}
.stButton>button:disabled {
  opacity: 0.5;
}
"""
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Helper function to extract location from URL or address
def parse_location_input(location_input):
    """Extract location from Google Maps URL or return plain address."""
    if not location_input:
        return None
    
    # Check if it's a Google Maps URL
    if "google.com/maps" in location_input.lower():
        try:
            # Try to extract place name from URL
            if "/place/" in location_input:
                place_name = location_input.split("/place/")[1].split("/")[0]
                place_name = place_name.replace("+", " ").split(",")[0]
                return place_name
        except:
            pass
        return "Kedah"  # Default extraction fallback
    
    # Return as-is if it's a plain address
    return location_input

# Functions
def get_gemini_response(symptoms, urgency, location=None):
    prompt = f"""
    Analyze the following patient symptoms and provide structured output:
    - Emergency level (Emergency / Urgent / Normal)
    - Should the patient call an ambulance? (Yes/No + reason)
    - Possible condition (general, not medical diagnosis)
    - Immediate first aid suggestions
    - Safety advice

    Symptoms: {symptoms}
    Urgency: {urgency}
    Location: {location if location else 'Not provided'}
    """
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3-flash-preview")
    response = model.generate_content(prompt)
    return response.text

# --- UI ---
st.markdown('<div class="hero-title">Emergency AI Health Support</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Describe your symptoms and get instant AI-powered emergency guidance.</div>', unsafe_allow_html=True)

with st.form("symptom_form"):
    symptoms = st.text_area("Describe your symptoms", max_chars=500, height=120)
    urgency = st.selectbox("Urgency level", ["Low", "Medium", "High"])
    location = st.text_input("Your location (city, postcode, or full address)", 
                             placeholder="e.g., Kedah, Malaysia or Kuala Lumpur")
    st.caption("💡 Tip: Enter a plain address (not a Google Maps URL)")
    submitted = st.form_submit_button("Analyze Symptoms")

ai_output = ""
emergency_level = ""
if submitted and symptoms.strip():
    # Parse and store location
    parsed_location = parse_location_input(location)
    if not parsed_location:
        st.error("❌ Please enter a valid location")
    else:
        # Store form data in session state
        st.session_state['symptoms'] = symptoms
        st.session_state['urgency'] = urgency
        st.session_state['location'] = parsed_location
        
        with st.spinner("Analyzing with AI..."):
                try:
                    ai_output = get_gemini_response(symptoms, urgency, parsed_location)
                except Exception as exc:
                    ai_output = ""
                    error_text = str(exc)
                    st.error("⚠️ AI service unavailable. Please try again later.")
                    if "quota" in error_text.lower() or "resource_exhausted" in error_text.lower():
                        st.warning("Your Gemini API quota is exhausted or rate limited. Wait a moment and try again.")
                    st.write(f"Error details: {error_text}")
                    st.stop()
        
        # Display AI results
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        for line in ai_output.split('\n'):
            if "Emergency level" in line:
                st.markdown(f"🚨 **{line}**")
            elif "Should the patient call an ambulance" in line:
                st.markdown(f"🧠 **{line}**")
            elif "Possible condition" in line:
                st.markdown(f"🩹 **{line}**")
            elif "Immediate first aid" in line:
                st.markdown(f"🩹 **{line}**")
            elif "Safety advice" in line or "Warning" in line:
                st.markdown(f"⚠️ **{line}**")
            else:
                st.markdown(line)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Emergency actions
        st.markdown("---")
        if emergency_level == "Emergency":
            st.button("🚑 Call Ambulance (999)", use_container_width=True)
        else:
            st.button("🚑 Call Ambulance", use_container_width=True)

st.markdown('<div class="disclaimer">⚠️ This is AI guidance, not medical advice. For emergencies, call your local emergency number immediately.</div>', unsafe_allow_html=True)
