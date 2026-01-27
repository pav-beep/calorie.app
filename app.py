import streamlit as st
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import json
import io

# --- CONFIGURATION ---
API_KEY = st.secrets["GOOGLE_API_KEY"]
ACCESS_CODE = st.secrets["APP_PASSWORD"] 

genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Calorie Track", layout="centered")

# --- HIDE STREAMLIT BRANDING ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp { margin-top: -80px; }
</style>
""", unsafe_allow_html=True)

# --- HELPER: IMAGE OVERLAY FUNCTION ---
def add_overlay(image, stats):
    """Draws stats and watermark on the image."""
    img = image.copy()
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # 1. Create a semi-transparent dark bar at the bottom
    # Bar height is 15% of image height
    bar_height = int(height * 0.15) 
    shape = [(0, height - bar_height), (width, height)]
    draw.rectangle(shape, fill=(0, 0, 0, 180)) # Black with transparency

    # 2. Load Fonts (Try to load a nice font, fallback to default)
    try:
        # Streamlit Cloud usually has DejaVuSans
        font_size = int(height * 0.05)
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        small_font = ImageFont.truetype("DejaVuSans.ttf", int(font_size * 0.6))
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # 3. Draw "Calorie Track" Watermark (Bottom Right)
    draw.text((width - width*0.05, height - bar_height + bar_height*0.6), 
              "Calorie Track AI", fill="yellow", font=small_font, anchor="rs")

    # 4. Draw Stats (Center of the bar)
    text = f"🔥 {stats['calories']} Cal  |  🥩 P: {stats['protein']}  |  🍞 C: {stats['carbs']}  |  🥑 F: {stats['fat']}"
    # Position text in the center of the bar
    draw.text((width/2, height - bar_height/2), text, fill="white", font=font, anchor="mm")
    
    return img

# --- PASSWORD LOGIC ---
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

def check_password():
    if st.session_state["password_correct"]:
        return True
    
    pwd = st.text_input("Enter Access Code:", type="password")
    if pwd == ACCESS_CODE:
        st.session_state["password_correct"] = True
        st.rerun()
    elif pwd:
        st.error("Incorrect Code")
    return False

# --- MAIN APP ---
if check_password():
    st.title("🥗 Calorie Track AI")
    st.write("Snap a pic. Get the stats. Share the progress.")

    uploaded_file = st.file_uploader("Upload meal photo", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Display original image
        image = Image.open(uploaded_file)
        st.image(image, caption='Your Meal', use_column_width=True)

        if st.button("Analyze & Generate Shareable"):
            with st.spinner('Calculating macros and generating watermark...'):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # We ask for JSON specifically to parse the numbers easily
                    prompt = """
                    Analyze this food image. Return a strictly valid JSON response.
                    Do not use Markdown formatting (no ```json).
                    Format:
                    {
                        "food_name": "Short name of dish",
                        "calories": "Estimated Total Calories (number only)",
                        "protein": "Protein in g (e.g. 30g)",
                        "carbs": "Carbs in g (e.g. 40g)",
                        "fat": "Fat in g (e.g. 15g)",
                        "brief_analysis": "One sentence summary."
                    }
                    """
                    
                    response = model.generate_content([prompt, image])
                    
                    # Clean response to ensure it's valid JSON
                    clean_text = response.text.strip().replace("```json", "").replace("```", "")
                    data = json.loads(clean_text)
                    
                    # 1. Show Data on Screen
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("Calories", data['calories'])
                    col2.metric("Protein", data['protein'])
                    col3.metric("Carbs", data['carbs'])
                    col4.metric("Fat", data['fat'])
                    st.info(f"AI Note: {data['brief_analysis']}")

                    # 2. Create Watermarked Image
                    processed_image = add_overlay(image, data)
                    
                    st.markdown("### 📸 Your Shareable Image")
                    st.image(processed_image, caption="Ready to share!", use_column_width=True)

                    # 3. Download Button
                    # Convert image to bytes for download
                    buf = io.BytesIO()
                    processed_image.save(buf, format="JPEG")
                    byte_im = buf.getvalue()

                    st.download_button(
                        label="📥 Download Image for Instagram/TikTok",
                        data=byte_im,
                        file_name="calorie_track_stats.jpg",
                        mime="image/jpeg",
                        use_container_width=True
                    )
                    
                    # 4. Social Links (Text Share)
                    share_text = f"I just tracked my meal: {data['calories']} Calories with Calorie Track AI! 💪"
                    share_url = "[https://YOUR-APP-LINK.streamlit.app](https://YOUR-APP-LINK.streamlit.app)" # Replace with your real link
                    
                    st.markdown(f"""
                    <div style="display: flex; gap: 10px; justify-content: center; margin-top: 20px;">
                        <a href="[https://wa.me/?text=](https://wa.me/?text=){share_text} {share_url}" target="_blank" style="text-decoration: none; background-color: #25D366; color: white; padding: 10px 20px; border-radius: 5px;">Share on WhatsApp</a>
                        <a href="[https://twitter.com/intent/tweet?text=](https://twitter.com/intent/tweet?text=){share_text}&url={share_url}" target="_blank" style="text-decoration: none; background-color: #1DA1F2; color: white; padding: 10px 20px; border-radius: 5px;">Share on X</a>
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error: {e}. Try a clearer photo.")
