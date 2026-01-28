import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import io
import pandas as pd
import extra_streamlit_components as stx
import datetime

# --- CONFIGURATION ---
# Add your Google Sheet Public Link in Streamlit Secrets as "SHEET_URL"
# Or paste it directly below (less secure but works for testing)
SHEET_URL = st.secrets["SHEET_URL"] 
API_KEY = st.secrets["GOOGLE_API_KEY"]

# Referral Codes (Simple List)
REFERRAL_CODES = ["FREE2026", "EARLYBIRD", "FRIEND50"]

genai.configure(api_key=API_KEY)
st.set_page_config(page_title="Calorie Track", layout="centered")

# --- COOKIE MANAGER (Keeps them logged in) ---
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# --- HIDE BRANDING ---
st.markdown("""<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>""", unsafe_allow_html=True)

# --- LOGIN LOGIC ---
def check_login():
    # 1. Check if Cookie exists
    user_cookie = cookie_manager.get(cookie="user_email")
    if user_cookie:
        return True, user_cookie

    st.title("🥗 Calorie Track AI")
    st.write("Please log in to continue.")
    
    # 2. Login Form
    with st.form("login_form"):
        user_input = st.text_input("Enter Email OR Referral Code")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            clean_input = user_input.strip().lower() # standardize input
            
            # Check A: Is it a Referral Code?
            if clean_input.upper() in REFERRAL_CODES:
                cookie_manager.set("user_email", f"Guest-{clean_input}", expires_at=datetime.datetime(2030, 1, 1))
                st.success("Referral Code Accepted!")
                st.rerun()
            
            # Check B: Is it a Paid Email? (Check Google Sheet)
            try:
                # Read the Google Sheet directly (Using the CSV export trick)
                # We modify the URL to export as CSV for Pandas to read
                csv_url = SHEET_URL.replace("/edit?usp=sharing", "/export?format=csv")
                df = pd.read_csv(csv_url)
                
                # Check if email exists in the 'email' column
                # We convert everything to lowercase to match safely
                valid_emails = df['email'].str.lower().tolist()
                
                if clean_input in valid_emails:
                    # VALID USER -> Set Cookie for 30 days
                    expires = datetime.datetime.now() + datetime.timedelta(days=30)
                    cookie_manager.set("user_email", clean_input, expires_at=expires)
                    st.success("Login Successful!")
                    st.rerun()
                else:
                    st.error("Access Denied. Please purchase access or check your email.")
            
            except Exception as e:
                st.error(f"Connection Error. Please try again. {e}")

    return False, None

# --- MAIN APP FLOW ---
is_logged_in, user_id = check_login()

if is_logged_in:
    # --- SHOW THE APP (Your existing code goes here) ---
    st.write(f"Logged in as: *{user_id}*")
    
    # [PASTE YOUR PREVIOUS IMAGE GENERATION CODE HERE]
    # (The code from the previous response starts here: uploaded_file = ...)
    uploaded_file = st.file_uploader("Upload meal photo", type=["jpg", "jpeg", "png"])
    
    # ... Rest of your logic ...
    
    # Add a Logout Button
    if st.button("Logout"):
        cookie_manager.delete("user_email")
        st.rerun()
