import streamlit as st
import re
from PIL import Image
import pandas as pd
from google import genai
from google.genai import types
import base64
import os
import time

# -----------------------------------------------------
# ૧. પેજ સેટિંગ
# -----------------------------------------------------
st.set_page_config(page_title="Gyan Live - TAT Mains Evaluation", page_icon="🎓", layout="centered")

# -----------------------------------------------------
# ૨. API Key અને મોડેલ
# -----------------------------------------------------
API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)
BEST_MODEL = "gemini-2.5-flash" 

# -----------------------------------------------------
# ૩. પ્રશ્નો અને મોબાઈલ લિસ્ટ લોડ કરવા (ગુગલ શીટ લિંક્સ)
# -----------------------------------------------------
BASE_Q_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQWh0A_30fkGqrbeerQhZkYFJpk37jai-Xy242HLGin-OaKt8I9_2gPl2g50eSEnAsOlQ3FMEhJHyj_/pub?gid=0&single=true&output=csv" 
BASE_AUTH_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQWh0A_30fkGqrbeerQhZkYFJpk37jai-Xy242HLGin-OaKt8I9_2gPl2g50eSEnAsOlQ3FMEhJHyj_/pub?gid=365490828&single=true&output=csv"

GOOGLE_SHEET_CSV_URL = f"{BASE_Q_URL}&nocache={int(time.time())}"
AUTH_SHEET_CSV_URL = f"{BASE_AUTH_URL}&nocache={int(time.time())}"

# લોડિંગ સિસ્ટમ - ક્લીન એન્ડ ડાયરેક્ટ
@st.cache_data(ttl=5)
def load_questions(url):
    try:
        df = pd.read_csv(url)
        q_dict = {}
        for col in df.columns:
            cat = str(col).strip()
            questions = df[col].dropna().astype(str).str.strip().tolist()
            numbered_questions = [f"{i+1}. {q}" if q != "Custom Question" else q for i, q in enumerate(questions)]
            q_dict[cat] = numbered_questions
        for cat in q_dict:
            if "Custom Question" not in q_dict[cat]: q_dict[cat].append("Custom Question")
        return q_dict
    except Exception as e:
        # જો શીટ કનેક્ટ ન થાય તો જૂનો ડેટા બતાવવાના બદલે લાઈવ સ્ક્રીન પર એરર બતાવશે
        st.error(f"⚠️ ગુગલ શીટમાંથી પ્રશ્નો લોડ થઈ શક્યા નથી! લિંક ચેક કરો. એરર: {e}")
        return {"સંપૂર્ણ પેપર (૧૦૦ ગુણ)": ["Custom Question"]}

@st.cache_data(ttl=5)
def load_allowed_numbers(url):
    try:
        df = pd.read_csv(url)
        first_col = df.columns[0]
        numbers = df[first_col].dropna().astype(str).str.strip().tolist()
        cleaned_numbers = [num.split('.')[0] for num in numbers]
        return cleaned_numbers
    except:
        return []

questions_dict = load_questions(GOOGLE_SHEET_CSV_URL)
allowed_numbers = load_allowed_numbers(AUTH_SHEET_CSV_URL)

# -----------------------------------------------------
# ૪. સ્ટેટ મેનેજમેન્ટ
# -----------------------------------------------------
if 'checking_result' not in st.session_state: st.session_state['checking_result'] = None
if 'user_authenticated' not in st.session_state: st.session_state['user_authenticated'] = False

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_base64 = get_base64_image("gyan logo.jpg")

# -----------------------------------------------------
# થીમ સેટિંગ્સ (CSS)
# -----------------------------------------------------
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Mukta+Vaani:wght@400;600;700;800&display=swap'); 
    * {{ font-family: 'Inter', 'Mukta Vaani', sans-serif !important; font-size: 17px !important; }}
    .stApp {{ background-color: #1e2026; color: #e3e4e8; }}
    .tat-title {{ color: #f1f2f5; text-align: center; font-size: 34px !important; font-weight: 800; margin-bottom: 25px; letter-spacing: -0.01em; }}
    label p {{ font-size: 18px !important; font-weight: 600 !important; color: #b2b5be !important; }}
    input, select, textarea {{ font-size: 17px !important; }}
    .question-box {{ background-color: #262933; border-left: 5px solid #707585; border-top: 1px solid #383c4a; border-right: 1px solid #383c4a; border-bottom: 1px solid #383c4a; padding: 20px; border-radius: 10px; font-size: 19px !important; color: #f1f2f5; margin-bottom: 20px; }}
    hr {{ border-color: #383c4a !important; }}
    button p {{ font-size: 18px !important; font-weight: 600 !important; }}
    .logo-container {{ text-align: center; margin-top: 15px; margin-bottom: 10px; }}
    .login-card {{ background-color: #262933; border: 1px solid #383c4a; padding: 30px; border-radius: 12px; margin-top: 20px; }}
</style>
""", unsafe_allow_html=True)

def create_html_report(text):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Gyan Live Result</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; color: #111; background-color: #fff; }}
            h2 {{ color: #4f8ef7; text-align: center; border-bottom: 2px solid #4f8ef7; padding-bottom: 10px; margin-bottom: 20px; }}
            .content {{ white-space: pre-wrap; font-size: 16px; }}
        </style>
    </head>
    <body>
        <h2>Gyan Live - TAT Mains Result</h2>
        <div class="content">{text}</div>
    </body>
    </html>
    """
    return html_content.encode('utf-8')

# -----------------------------------------------------
# ૫. મુખ્ય ઇન્ટરફેસ
# -----------------------------------------------------
try: st.image("Seminar Uma Academy.jpg", use_container_width=True)
except: pass

if logo_base64:
    st.markdown(f"""<div class="logo-container"><img src="data:image/jpeg;base64,{logo_base64}" width="180" style="border-radius: 10px;"></div>""", unsafe_allow_html=True)

st.markdown("<div class='tat-title'>GyanLive Evaluator-TAT Descriptive</div>", unsafe_allow_html=True)

if not st.session_state['user_authenticated']:
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)
    st.markdown("### 🔐 Student Access Verification")
    input_phone = st.text_input("કૃપા કરીને તમારો રજિસ્ટર્ડ મોબાઈલ નંબર દાખલ કરો:", max_chars=10, placeholder="10-digit mobile number")
    
    if st.button("Verify Number ➔", use_container_width=True, type="primary"):
        cleaned_phone = str(input_phone).strip()
        if cleaned_phone in allowed_numbers:
            st.session_state['user_authenticated'] = True
            st.success("✅ એક્સેસ મંજૂર કરવામાં આવ્યો છે!")
            st.rerun()
        else:
            st.error("❌ આ મોબાઈલ નંબર જ્ઞાન લાઈવની રજિસ્ટર્ડ લિસ્ટમાં ઉપલબ્ધ નથી!")
    st.markdown("</div>", unsafe_allow_html=True)

else:
    category = st.selectbox("વિભાગ:", list(questions_dict.keys()))
    selected_display = st.selectbox("વિષય/પ્રશ્ન પસંદ કરો:", questions_dict[category])

    actual_q = re.sub(r'^\d+\. ', '', selected_display) if selected_display != "Custom Question" else ""
    if actual_q: st.markdown(f"<div class='question-box'><strong>પસંદ કરેલ પ્રશ્ન:</strong><br>{actual_q}</div>", unsafe_allow_html=True)
        
    final_question_to_check = actual_q if actual_q else st.text_area("તમારો પ્રશ્ન:")

    uploaded_files = st.file_uploader("PDF અથવા ફોટા પસંદ કરો", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

    st.warning("⚠️ **Disclaimer:** This tool is using AI for evaluation and requires clear, proper handwriting.")

    if st.button("Evaluate 🚀", type="primary", use_container_width=True):
        if not uploaded_files:
            st.warning("⚠️ ફાઈલ અપલોડ કરો.")
        else:
            with st.spinner("Working on it"):
                try:
                    if category == "સંપૂર્ણ પેપર (૧૦૦ ગુણ)":
                        total_marks = 100
                        max_marks_allowed = "લાગુ પડતું નથી"
                        expected_words = "દરેક વિભાગની માંગ મુજબ"
                        category_rules = "✅ ૧૦૦ માર્કનું સંપૂર્ણ વર્ણનાત્મક પેપર ચેક કરવું."
                    elif category == "નિબંધ લેખન":
                        total_marks = 20
                        max_marks_allowed = 14
                        expected_words = "આશરે ૨૫૦ થી ૩૦૦ શબ્દો"
                        category_rules = "✅ હકારાત્મક ગુણ: પ્રસ્તાવના, વિષયવસ્તુ, મૌલિકતા, ભાષા."
                    elif category == "ચર્ચાપત્ર":
                        total_marks = 10
                        max_marks_allowed = 6
                        expected_words = "આશરે ૨૦0 શબ્દો"
                        category_rules = "✅ હકારાત્મક ગુણ: ફોર્મેટ, તટસ્થ રજૂઆત, સૂચનો."
                    elif category == "પત્ર લેખન":
                        total_marks = 10
                        max_marks_allowed = 6
                        expected_words = "આશરે ૧૦0 શબ્દો"
                        category_rules = "✅ હકારાત્મક ગુણ: સત્તાવાર ફોર્મેટ, સચોટ વિષયવસ્તુ."
                    elif category == "સંક્ષેપીકરણ":
                        total_marks = 10
                        max_marks_allowed = 5
                        expected_words = "આશરે ૧/૩ ભાગ"
                        category_rules = "✅ હકારાત્મક ગુણ: યોગ્ય શીર્ષક, મૂળ વિચારની જાળવણી."
                    else: 
                        total_marks = 20
                        max_marks_allowed = 20
                        expected_words = "૨૦ પ્રશ્નોના ટૂંકા જવાબો"
                        category_rules = "✅ વ્યાકરણ સંપૂર્ણ સાચું હોય તો જ ૧ માર્ક આપવો, ભૂલ હોય તો સીધો ૦."

                    prompt = f"""
                    તમે Gyan Live ના અત્યંત હોશિયાર, કડક અને સચોટ TAT 2026 મેઈન્સ ના પેપર ચેકર છો. 
                    વિદ્યાર્થીએ '{category}' વિભાગમાં '{final_question_to_check}' વિષય પર જવાબ લખ્યો છે.
                    تમારો જવાબ હંમેશા આ વાક્યથી જ શરૂ કરો: "તમારા જવાબનું સચોટ અને વિસ્તૃત મૂલ્યાંકન નીચે મુજબ છે:"
                    
                    ### ૧. અંદાજિત શબ્દ સંખ્યા અને એનાલિસિસ: 
                    ### ૨. ક્યાં માર્કસ કપાયા અને શા માટે? (Errors Analysis): 
                    ### ૩. વિભાગવાર માર્કિંગ અને મેળવેલ ગુણ (Out of {total_marks}): 
                    ### ૪. ભૂલોનું લિસ્ટ (સચોટ ચેકિંગ): 
                    ### ૫. વિસ્તૃત સલાહ અને માર્ગદર્શન (Expert Advice): 
                    """
                    
                    contents = [prompt]
                    for file in uploaded_files:
                        if file.type == "application/pdf": contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                        else: contents.append(Image.open(file))
                    
                    response = client.models.generate_content(model=BEST_MODEL, contents=contents, config=types.GenerateContentConfig(temperature=0.0))
                    st.session_state['checking_result'] = response.text
                    st.rerun()
                except Exception as e: st.error(f"❌ ભૂલ: {e}")

    if st.session_state['checking_result']:
        st.markdown("<hr>", unsafe_allow_html=True)
        st.success("✅ ચેકિંગ પૂર્ણ!")
        st.markdown(st.session_state['checking_result'])
        
        report_data = create_html_report(st.session_state['checking_result'])
        st.download_button(
            label="📥 રિઝલ્ટ ડાઉનલોડ કરો",
            data=report_data,
            file_name="Gyan_Live_Result.html",
            mime="text/html",
            use_container_width=True
        )
