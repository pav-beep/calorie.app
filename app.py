import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import plotly.graph_objects as go
import json
import time
import requests
import base64
from PIL import Image
from io import BytesIO

# --- 1. CONFIGURATION & MODERN THEME ---
st.set_page_config(page_title="Kalsoma", page_icon="🦁", layout="centered")

# LINKS TO IMAGES (You can replace these with your own GitHub links later)
BANNER_URL = "https://images.unsplash.com/photo-1490645935967-10de6ba17061?q=80&w=2053&auto=format&fit=crop" # Luxury Food Dark
LOGO_URL = "https://cdn-icons-png.flaticon.com/512/616/616490.png" # Gold Lion Placeholder

st.markdown(f"""
<style>
    /* IMPORT GOOGLE FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Poppins:wght@400;600&display=swap');

    /* APP BACKGROUND */
    .stApp {{ background-color: #FAFAFA; font-family: 'Poppins', sans-serif; }}

    /* TYPOGRAPHY */
    h1, h2, h3 {{ font-family: 'Playfair Display', serif; color: #111 !important; }}
    p, div, label {{ font-family: 'Poppins', sans-serif; color: #555; }}

    /* HERO BANNER - This removes the top padding to make image full width */
    .block-container {{ padding-top: 0rem; padding-bottom: 5rem; }}
    
    /* CUSTOM HERO SECTION */
    .hero-container {{
        position: relative;
        width: 100%;
        height: 250px;
        background-image: linear-gradient(to bottom, rgba(0,0,0,0.3), rgba(255,255,255,1)), url('{BANNER_URL}');
        background-size: cover;
        background-position: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 30px;
    }}
    .hero-logo {{
        width: 80px;
        height: 80px;
        background: white;
        border-radius: 50%;
        padding: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin-bottom: 10px;
    }}
    .hero-title {{
        color: #111;
        font-size: 40px;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 2px 4px rgba(255,255,255,0.8);
        letter-spacing: 2px;
    }}
    .hero-subtitle {{
        color: #333;
        font-size: 14px;
        font-weight: 600;
        background: rgba(255,255,255,0.8);
        padding: 5px 15px;
        border-radius: 20px;
    }}

    /* GOLD BUTTONS */
    .stButton>button {{
        background: linear-gradient(135deg, #D4AF37 0%, #C5A028 100%);
        color: white !important;
        border-radius: 50px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.4);
        width: 100%;
        height: 55px;
        font-size: 16px;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.6);
    }}

    /* MODERN CARDS */
    div.css-card {{
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        border: 1px solid #F0F0F0;
        text-align: center;
        transition: transform 0.2s;
    }}
    div.css-card:hover {{
        transform: scale(1.02);
    }}
    div.css-card h3 {{ color: #D4AF37 !important; margin: 0; font-size: 28px; }}
    div.css-card p {{ margin: 0; font-size: 12px; color: #888; letter-spacing: 1px; text-transform: uppercase; }}

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 15px; background-color: rgba(255,255,255,0.95); padding: 15px;
        position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
        width: 90%; max-width: 500px;
        z-index: 999;
        border-radius: 100px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        justify-content: center;
        backdrop-filter: blur(10px);
    }}
    .stTabs [aria-selected="true"] {{ background-color: #111; color: white; border-radius: 50px; }}
    
    /* INPUTS */
    .stTextInput>div>div>input {{
        background-color: #FFFFFF;
        border-radius: 15px;
        border: 2px solid #F0F0F0;
        color: #333;
        padding: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. BACKEND CONNECTION ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    SHEET_URL = "https://docs.google.com/spreadsheets/d/1s2GopKvY30MlN9_8hqMAsrpr_fUcNjUvPkA6IYHuJo8/edit"
    CREDS_DICT = st.secrets["gcp_service_account"]
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDS_DICT, scope)
    client = gspread.authorize(creds)
except Exception as e:
    st.error(f"Startup Error: {e}")
    st.stop()

# --- 3. HELPER FUNCTIONS ---
def get_db():
    return client.open_by_url(SHEET_URL)

def ai_analyze_image_direct(image):
    try:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Using LATEST alias
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": "Act as Kalsoma Coach. Analyze this food image. 1. Identify food. 2. Estimate Cals/Pro/Carb/Fat. 3. Warn about sauces/oils. 4. List 2 micros. Return strictly JSON: {\"food_name\": \"...\", \"calories\": 0, \"protein\": 0, \"carbs\": 0, \"fat\": 0, \"warning\": \"...\", \"micros\": \"...\"}"},
                    {"inline_data": { "mime_type": "image/jpeg", "data": img_str }}
                ]
            }]
        }
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        if response.status_code != 200: return None, f"Google API Error: {response.text}"
        result = response.json()
        try: return result['candidates'][0]['content']['parts'][0]['text'], None
        except: return None, "AI response was empty."
    except Exception as e: return None, str(e)

def get_dashboard_data(email):
    try:
        sheet = get_db().worksheet("Logs")
        all_logs = sheet.get_all_records()
        df = pd.DataFrame(all_logs)
        if df.empty: return 0, 0, 0, 0, []
        df['date_only'] = pd.to_datetime(df['timestamp']).dt.date
        today = datetime.date.today()
        daily = df[(df['email'] == email) & (df['date_only'] == today)]
        if daily.empty: return 0, 0, 0, 0, []
        return (daily['calories'].sum(), daily['protein'].sum(), daily['carbs'].sum(), daily['fat'].sum(), daily.to_dict('records'))
    except: return 0, 0, 0, 0, []

# --- 4. APP NAVIGATION ---
if 'page' not in st.session_state: st.session_state['page'] = 'LOGIN'

if st.session_state['page'] == 'LOGIN':
    # LUXURY LOGIN SCREEN
    st.markdown(f"""
    <div class="hero-container" style="height: 300px; border-radius: 0 0 30px 30px;">
        <img src="{LOGO_URL}" class="hero-logo">
        <h1 class="hero-title">KALSOMA</h1>
        <div class="hero-subtitle">THE GOLD STANDARD</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("### Member Access")
        email = st.text_input("Email Address", placeholder="Enter your email")
        code = st.text_input("Access Code", placeholder="Optional")
        if st.form_submit_button("ENTER SANCTUARY"):
            if email:
                st.session_state['user_email'] = email
                st.session_state['page'] = 'APP'
                st.rerun()

elif st.session_state['page'] == 'APP':
    # CUSTOM HEADER FOR APP PAGE
    st.markdown(f"""
    <div class="hero-container" style="height: 180px; margin-bottom: 20px;">
        <div style="display:flex; align-items:center; gap: 15px;">
            <img src="{LOGO_URL}" style="width:50px; height:50px; background:white; border-radius:50%; padding:5px;">
            <div>
                <h2 style="margin:0; font-size:24px;">Hello, {st.session_state['user_email'].split('@')[0]}</h2>
                <p style="margin:0; color:#333; font-weight:600;">Let's hit your targets.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["📊 DASH", "📸 SCAN", "🏆 TRIBE"])
    
    with t1:
        cals, pro, carb, fat, logs = get_dashboard_data(st.session_state['user_email'])
        target = 2400
        remaining = max(0, target - cals)
        
        # LUXURY ARC GAUGE
        fig = go.Figure(go.Indicator(
            mode = "gauge+number", 
            value = remaining, 
            title = {'text': "CALORIES REMAINING", 'font': {'size': 12, 'color': "gray", 'family': "Poppins"}}, 
            number = {'font': {'size': 50, 'color': "#D4AF37", 'family': "Playfair Display", 'weight': 800}}, 
            gauge = {
                'axis': {'range': [0, target], 'visible': False}, 
                'bar': {'color': "#D4AF37"}, 
                'bgcolor': "#F5F5F5", 
                'borderwidth': 0, 
                'shape': "angular"
            }
        ))
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=0, b=0, l=20, r=20), height=240)
        st.plotly_chart(fig, use_container_width=True)
        
        # MODERN MACRO CARDS
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='css-card'><h3>{pro}g</h3><p>PROTEIN</p></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='css-card'><h3>{carb}g</h3><p>CARBS</p></div>", unsafe_allow_html=True)
        with c3: st.markdown(f"<div class='css-card'><h3>{fat}g</h3><p>FAT</p></div>", unsafe_allow_html=True)
        
        # LOG HISTORY
        st.markdown("<br><h3 style='font-size: 18px;'>Today's Ledger</h3>", unsafe_allow_html=True)
        if logs:
            for log in logs: st.markdown(f"<div style='background:white; padding:15px; border-radius:15px; margin-bottom:10px; border:1px solid #EEE; box-shadow: 0 2px 5px rgba(0,0,0,0.02); display:flex; justify-content:space-between; align-items:center;'><b>{log['food_name']}</b> <span style='color:#D4AF37; font-weight:bold;'>{log['calories']} kcal</span></div>", unsafe_allow_html=True)
    
    with t2:
        st.markdown("<h3 style='text-align:center;'>The Coach's Eye</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:12px;'>Snap a photo. Get instant macro data.</p>", unsafe_allow_html=True)
        img_file = st.camera_input("Snap your meal")
        if img_file:
            st.image(img_file, use_container_width=True)
            if st.button("ANALYZE MEAL"):
                with st.spinner("Consulting the database..."):
                    img = Image.open(img_file)
                    raw_text, error_msg = ai_analyze_image_direct(img)
                    if raw_text:
                        try:
                            clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                            data = json.loads(clean_json)
                            st.session_state['scan_data'] = data
                        except: st.error("AI Error. Please try again.")
                    elif error_msg: st.error(f"Error: {error_msg}")
        if 'scan_data' in st.session_state:
            data = st.session_state['scan_data']
            if data.get('warning'): st.warning(f"⚠️ {data['warning']}")
            st.markdown(f"<div style='text-align:center; margin: 20px 0;'><h3>{data['food_name']}</h3></div>", unsafe_allow_html=True)
            
            c1, c2 = st.columns(2)
            nc = c1.number_input("Calories", value=data['calories'])
            np = c2.number_input("Protein", value=data['protein'])
            ncarb = c1.number_input("Carbs", value=data['carbs'])
            nfat = c2.number_input("Fat", value=data['fat'])
            if st.button("ADD TO LEDGER"):
                try:
                    sheet = get_db().worksheet("Logs")
                    sheet.append_row([st.session_state['user_email'], str(datetime.datetime.now()), data['food_name'], nc, np, ncarb, nfat, data['micros']])
                    st.success("Entry Logged.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Save failed: {e}")
    with t3:
        st.header("The Tribe")
        st.info("Community Leaderboards coming in V2.")
