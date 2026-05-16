import streamlit as st
import re
from PIL import Image
import pandas as pd
from google import genai
from google.genai import types
import base64
import os

# -----------------------------------------------------
# ૧. પેજ સેટિંગ
# -----------------------------------------------------
st.set_page_config(page_title="Gyan Live - TAT Mains Evaluation", page_icon="🎓", layout="centered")

# -----------------------------------------------------
# ૨. API Key અને મોડેલ (UPDATED: સેટ કરાયું લેટેસ્ટ મોડેલ)
# -----------------------------------------------------
API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)
BEST_MODEL = "gemini-2.5-flash"  # મોડેલ ૨.૫ ફ્લેશ કરવાથી સ્પીડ વધશે

# -----------------------------------------------------
# ૩. પ્રશ્નો લોડ કરવા 
# -----------------------------------------------------
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSb-F79599XF_5vjBv_Wb9Y-vM6MhEAtHj6R7fB-cWreKAnUo0VwNEX9tIeXJ9Wq0_kUds-Z1V9oX8z/pub?output=csv" 

@st.cache_data(ttl=60)
def load_questions(url):
    fallback_questions = {
        "સંપૂર્ણ પેપર (૧૦૦ ગુણ)": ["૧. આખું TAT મેઈન્સ પેપર (તમામ પ્રશ્નો)", "Custom Question"],
        "નિબંધ લેખન": ["૧. આર્ટિફિશિયલ ઇન્ટેલિજન્સ: વરદાન કે અભિશાપ?", "Custom Question"],
        "ચર્ચાપત્ર": ["૧. ટ્રાફિક સમસ્યા અંગે તંત્રીને પત્ર", "Custom Question"],
        "પત્ર લેખન": ["૧. અનિયમિત વીજ પુરવઠા અંગે ફરિયાદ પત્ર", "Custom Question"],
        "સંક્ષેપીકરણ": ["૧. સંક્ષેપીકરણ ફકરો - ૧", "Custom Question"],
        "વ્યાકરણ (૨૦ ગુણ)": ["૧. વ્યાકરણ સેટ - ૧", "Custom Question"]
    }
    try:
        df = pd.read_csv(url)
        q_dict = {"સંપૂર્ણ પેપર (૧૦૦ ગુણ)": ["૧. આખું TAT મેઈન્સ પેપર (તમામ પ્રશ્નો)", "Custom Question"]}
        for col in df.columns:
            cat = str(col).strip()
            questions = df[col].dropna().astype(str).str.strip().tolist()
            numbered_questions = [f"{i+1}. {q}" if q != "Custom Question" else q for i, q in enumerate(questions)]
            q_dict[cat] = numbered_questions
        for cat in q_dict:
            if "Custom Question" not in q_dict[cat]: q_dict[cat].append("Custom Question")
        return q_dict
    except: return fallback_questions

questions_dict = load_questions(GOOGLE_SHEET_CSV_URL)

# -----------------------------------------------------
# ૪. સ્ટેટ મેનેજમેન્ટ
# -----------------------------------------------------
if 'checking_result' not in st.session_state: st.session_state['checking_result'] = None

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

logo_base64 = get_base64_image("gyan logo.jpg")

# -----------------------------------------------------
# પ્રીમિયમ ગ્રે થીમ અને લાર્જ ફોન્ટ ઈન્ટરફેસ (CSS)
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
# ૬. મુખ્ય પોર્ટલ ડેશબોર્ડ
# -----------------------------------------------------
try: st.image("Seminar Uma Academy.jpg", use_container_width=True)
except: pass

if logo_base64:
    st.markdown(f"""<div class="logo-container"><img src="data:image/jpeg;base64,{logo_base64}" width="180" style="border-radius: 10px;"></div>""", unsafe_allow_html=True)

st.markdown("<div class='tat-title'>GyanLive Evaluator-TAT Descriptive</div>", unsafe_allow_html=True)

category = st.selectbox("વિભાગ:", list(questions_dict.keys()))
selected_display = st.selectbox("વિષય/પ્રશ્ન પસંદ કરો:", questions_dict[category])

actual_q = re.sub(r'^\d+\. ', '', selected_display) if selected_display != "Custom Question" else ""
if actual_q: st.markdown(f"<div class='question-box'><strong>પસંદ કરેલ પ્રશ્ન:</strong><br>{actual_q}</div>", unsafe_allow_html=True)
    
final_question_to_check = actual_q if actual_q else st.text_area("તમારો પ્રશ્ન:")

uploaded_files = st.file_uploader("PDF અથવા ફોટા પસંદ કરો (આખું પેપર હોય તો બધી ફાઈલો સિલેક્ટ કરો)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

st.warning("⚠️ **Disclaimer:** This tool is using AI for evaluation and requires clear, proper handwriting for accurate factual mapping and results.")

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
                    category_rules = """
                    ✅ **ખાસ સૂચના (સંપૂર્ણ પેપર માટે):** વિદ્યાર્થીએ આખું 100 માર્કનું પેપર અપલોડ કર્યું છે. દરેક પ્રશ્નનું અલગ-અલગ મૂલ્યાંકન નીચે મુજબના કડક માપદંદોથી કરવું:
                    ૧. નિબંધ (૨૦ ગુણ): આશરે ૨૫૦ થી ૩૦૦ શબ્દો. મહત્તમ ૧૪ ગુણ. હકારાત્મક: પ્રસ્તાવના(૪), વિષયવસ્તુ(૮), મૌલિકતા(૪), ભાષા(૪). નકારાત્મક: વિષયાંતર(-૩ થી -૫), શબ્દમર્યાદા ભંગ(-૧ થી -૨).
                    ૨. સંક્ષેપીકરણ (૨ પ્રશ્નો, કુલ ૨૦ ગુણ): ૧/૩ ભાગ. પ્રત્યેકમાં મહત્તમ ૫ ગુણ. હકારાત્મક: શીર્ષક(૨), મૂળ વિચાર(૩), મૌલિકતા(૩), લંબાઈ(૨). નકારાત્મક: શીર્ષક વગર(-૨), કોપી-પેસ્ટ(-૩).
                    ૩. પત્ર લેખન (૨ પ્રશ્નો, કુલ ૨૦ ગુણ): દરેકના આશરે ૧૦૦ શબ્દો. પ્રત્યેકમાં મહત્તમ ૬ ગુણ. હકારાત્મક: ફોર્મેટ(૩), સચોટતા(૪), સત્તાવાર ભાષા(૩). નકારાત્મક: માળખાકીય ભૂલ(-૧), અસ્પષ્ટતા(-૨).
                    ૪. ચર્ચાપત્ર (૨ પ્રશ્નો, કુલ ૨૦ ગુણ): દરેકના આશરે ૨૦0 શબ્દો. પ્રત્યેકમાં મહત્તમ ૬ ગુણ. હકારાત્મક: ફોર્મેટ(૨), તટસ્થ રજૂઆત(૩), સૂચનો(૩), ભાષા(૨). નકારાત્મક: ફોર્મેટ ભૂલ(-૧ પ્રતિ ભૂલ).
                    ૫. વ્યાકરણ (૨૦ પ્રશ્નો, ૨૦ ગુણ): ૧૦ અલગ-અલગ ટોપિક છે (રૂઢિપ્રયોગ, કહેવતો, સમાસ, છંદ, અલંકાર, શબ્દસમૂહ, જોડણી, લેખનશુદ્ધિ, સંધિ, વાક્ય રચના). દરેક ટોપિકમાંથી ફરજિયાત ૨ પ્રશ્નો પૂછાયા હશે. દરેક સાચા જવાબનો ૧ ગુણ, સહેજ પણ ભૂલ હોય તો સીધો ૦ ગુણ.
                    """
                elif category == "નિબંધ લેખન":
                    total_marks = 20
                    max_marks_allowed = 14
                    expected_words = "આશરે ૨૫૦ થી ૩૦૦ શબ્દો"
                    category_rules = """
                    ✅ હકારાત્મક ગુણ: પ્રસ્તાવના/ઉપસંહાર (૪ ગુણ), વિષયવસ્તુ/ઊંડાણ (૮ ગુણ), મૌલિકતા/તાર્કિક પ્રવાહ (૪ ગુણ), ભાષાકીય શુદ્ધિ (૪ ગુણ).
                    ❌ નકારાત્મક ગુણ: વિષયાંતર (-૩ થી -૫ ગુણ), મૌલિકતાનો અભાવ (-૨ ગુણ), શબ્દમર્યાદા ભંગ (-૧ થી -૨ ગુણ).
                    """
                elif category == "ચર્ચાપત્ર":
                    total_marks = 10
                    max_marks_allowed = 6
                    expected_words = "આશરે ૨૦૦ શબ્દો"
                    category_rules = """
                    ✅ હકારાત્મક ગુણ: ફોર્મેટ (કાલ્પનિક સરનામું, તંત્રીશ્રી, વિષય, સંબોધન) (૨ ગુણ), તટસ્થ રજૂઆત (૩ ગુણ), રચનાત્મક સૂચનો (૩ ગુણ), ઔપಚಾರિક ભાષા (૨ ગુણ).
                    ❌ નકારાત્મક ગુણ: ફોર્મેટ ભૂલ (-૧ ગુણ પ્રતિ ભૂલ), અંગત/ઉગ્ર ભાષા (-૧.૫ ગુણ).
                    """
                elif category == "પત્ર લેખન":
                    total_marks = 10
                    max_marks_allowed = 6
                    expected_words = "આશરે ૧૦૦ શબ્દો"
                    category_rules = """
                    ✅ હકારાત્મક ગુણ: સત્તાવાર ફોર્મેટ (૩ ગુણ), સચોટ વિષયવસ્તુ/To the point (૪ ગુણ), સત્તાવાર શબ્દાવલિ (૩ ગુણ).
                    ❌ નકારાત્મક ગુણ: માળખાકીય ભૂલો (-૧ થી -૨ ગુણ), અસ્પષ્ટતા (-૧.૫ થી -૨ ગુણ), બિનઔપಚಾರિક ભાષા (-૧ ગુણ).
                    """
                elif category == "સંક્ષેપીકરણ":
                    total_marks = 10
                    max_marks_allowed = 5
                    expected_words = "આપેલ ગદ્યમાંથી આશરે ૧/૩ (ત્રીજો) ભાગ"
                    category_rules = """
                    ✅ હકારાત્મક ગુણ: યોગ્ય શીર્ષક (૨ ગુણ), મૂળ વિચારની જાળવણી (૩ ગુણ), મૌલિકતા/પોતાના શબ્દોમાં (૩ ગુણ), લંબાઈ અને શુદ્ધિ (૨ ગુણ).
                    ❌ નકારાત્મક ગુણ: શીર્ષકનો અભાવ (-૨ ગુણ), કોપી-પેસ્ટ (-૨ થી -૩ ગુણ), અર્થનો અનર્થ (-૧.૫ ગુણ).
                    """
                else: 
                    total_marks = 20
                    max_marks_allowed = 20
                    expected_words = "શબ્દમર્યાદા લાગુ પડતી નથી (૨૦ પ્રશ્નોના ટૂંકા જવાબો)"
                    category_rules = """
                    ✅ નિયમ: વ્યાકરણના ૧૦ અલગ-અલગ ટોપિક છે (રૂઢિપ્રયોગ, કહેવતો, સમાસ, છંદ, અલંકાર, શબ્દસમૂહ, જોડણી, લેખનશુદ્ધિ, સંધિ, વાક્ય રચના). દરેક ટોપિકમાંથી ફરજિયાત ૨ પ્રશ્નો પૂછાયા હશે, એમ કુલ ૨૦ પ્રશ્નો હશે. દરેક પ્રશ્નનો ૧ ગુણ છે. (કુલ ૨૦ ગુણ).
                    ✅ હકારાત્મક ગુણ: જો જવાબ વ્યાકરણની દૃષ્ટિએ અને જોડણીની દૃષ્ટિએ સંપૂર્ણ સાચો હોય તો પૂરો ૧ ગુણ આપવો.
                    ❌ નકારાત્મક ગુણ: જો જવાબ ખોટો હોય, અથવા જવાબ સાચો હોય પણ તેમાં જોડણીની સહેજ પણ ભૂલ હોય, તો સીધો ૦ (ઝીરો) ગુણ આપવો. કોઈપણ પ્રશ્નમાં અડધો (૦.૫) ગુણ આપવો જ નહીં.
                    """

                prompt = f"""
                તમે Gyan Live ના અત્યંત હોશિયાર, કડક અને સચોટ TAT 2026 મેઈન્સ (ગુજરાતી વર્ણનાત્મક) ના પેપર ચેકર છો. 
                વિદ્યાર્થીએ '{category}' વિભાગમાં '{final_question_to_check}' વિષય પર જવાબ લખ્યો છે.
                
                તમારો જવાબ હંમેશા આ વાક્યથી જ શરૂ કરો: "તમારા જવાબનું સચોટ અને વિસ્તૃત મૂલ્યાંકન નીચે મુજબ છે:"

                📏 વિભાગ અને માર્કિંગના કડક નિયમો:
                - આ પ્રશ્ન કુલ {total_marks} ગુણનો છે.
                - શબ્દમર્યાદા: {expected_words} હોવી જોઈએ.
                - સૌથી કડક નિયમ (આંતરિક - રિઝલ્ટમાં ન લખવો): ગમે તેટલો સારો જવાબ હોય, પણ દર્શાવેલ મહત્તમ લિમિટ ({max_marks_allowed}) થી વધુ ગુણ આપવા જ નહીં. માત્ર '{total_marks} માંથી મેળવેલ ગુણ' જ દર્શાવવા.

                {category_rules}

                ⚠️ ભાષા, મૌલિકતા અને નકારાત્મક માર્કિંગ (Negative Marking):
                - અંગ્રેજી શબ્દોનો નિષેધ: લખાણમાં અંગ્રેજી મૂળાક્ષરો (A-Z) નો પ્રયોગ સદંતર ટાળવો. જો એવો કોઈ શબ્દ હોય જેનું ગુજરાતી શક્ય જ ન હોય, તો તેનો ઉચ્ચાર ફરજિયાત ગુજરાતી લિપિમાં જ લખેલો હોવો જોઈએ (દા.ત. ઇન્ટરનેટ). જો લખાણમાં અંગ્રેજી અક્ષરો દેખાય તો માર્ક કાપવા અને સલાહમાં ટકોર કરવી.
                - મૌલિકતા: ગોખેલું કે ચીલાચાલુ લખાણ હોય તો માર્ક કાપવા, લખાણ મૌલિક અને હકારાત્મક હોવું જોઈએ.
                - દર ૩ જોડણી કે વાક્યરચનાની ભૂલ પર -૦.૫ ગુણ કાપવા.
                - પત્ર/ચર્ચાપત્રમાં જો વિદ્યાર્થીએ સાચું નામ (દા.ત. ધવલ, પટેલ, વિસનગર) લખ્યું હોય તો ઓળખ છતી કરવા બદલ સીધા -૨ ગુણ કાપવા.

                મૂલ્યાંકન નીચેના ૫ વિભાગમાં જ સુંદર રીતે આપવું:
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
