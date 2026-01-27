import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURATION ---
# We will set these in Streamlit Cloud "Secrets" later to keep them safe
API_KEY = st.secrets["GOOGLE_API_KEY"]
ACCESS_CODE = st.secrets["APP_PASSWORD"] 

# Configure Gemini
genai.configure(api_key=API_KEY)

# --- PAGE SETUP ---
st.set_page_config(page_title="AI Nutritionist", layout="centered")

# --- HIDE STREAMLIT BRANDING (Optional) ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- PASSWORD PROTECTION ---
def check_password():
    """Returns `True` if the user had the correct password."""
    def password_entered():
        if st.session_state["password"] == ACCESS_CODE:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # clear password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Enter Access Code (Provided after purchase):", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input again.
        st.text_input(
            "Enter Access Code (Provided after purchase):", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Access code incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    # --- MAIN APP ---
    st.title("🥗 AI Calorie Scanner")
    st.write("Upload a photo of your meal for an instant breakdown.")

    uploaded_file = st.file_uploader("Choose a food image...", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption='Your Meal', use_column_width=True)

        if st.button("Analyze Calories"):
            with st.spinner('Analyzing food components...'):
                try:
                    # We use Gemini 1.5 Flash for speed and higher free limits
                    # If you need extreme accuracy, change to 'gemini-1.5-pro' 
                    # but be aware 'pro' has very low limits on the free tier (2 req/min).
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    prompt = """
                    You are an expert nutritionist. Analyze this image.
                    1. Identify all food items.
                    2. Estimate portion size.
                    3. Calculate calories and macros (Protein, Carbs, Fat).
                    4. Provide a total calorie count.
                    
                    Format the output clearly with bold headings and a final "TOTAL ESTIMATE".
                    """
                    
                    response = model.generate_content([prompt, image])
                    st.markdown(response.text)
                    st.success("Analysis Complete!")
                    
                except Exception as e:
                    st.error(f"Error: {e}")
