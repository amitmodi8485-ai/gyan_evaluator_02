import streamlit as st
import re
from PIL import Image
import pandas as pd
from google import genai
from google.genai import types

# -----------------------------------------------------
# ૧. પેજ સેટિંગ
# -----------------------------------------------------
st.set_page_config(page_title="Gyan Academy - TAT Mains Evaluation", page_icon="🎓", layout="centered")

# -----------------------------------------------------
# ૨. API Key અને મોડેલ
# -----------------------------------------------------
API_KEY = st.secrets["GEMINI_API_KEY"] 
client = genai.Client(api_key=API_KEY)
BEST_MODEL = "gemini-flash-latest" 

# -----------------------------------------------------
# ૩. પ્રશ્નો લોડ કરવા 
# -----------------------------------------------------
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSdEfCcM_cugFgMBsSlnsV_Lx1azdZgtNNivsApg1KWbFaE_24iMLFYvbkC8HMBg0xuKdsfbj6VxDZa/pub?output=csv" 

@st.cache_data(ttl=60)
def load_questions(url):
    fallback_questions = {
        "સંપૂર્ણ પેપર (૧૦૦ ગુણ)": ["૧. આખું TAT મેઈન્સ પેપર (તમામ પ્રશ્નો)", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "નિબંધ લેખન": ["૧. આર્ટિફિશિયલ ઇન્ટેલિજન્સ: વરદાન કે અભિશાપ?", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "ચર્ચાપત્ર": ["૧. ટ્રાફિક સમસ્યા અંગે તંત્રીને પત્ર", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "પત્ર લેખન": ["૧. અનિયમિત વીજ પુરવઠા અંગે ફરિયાદ પત્ર", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "સંક્ષેપીકરણ": ["૧. સંક્ષેપીકરણ ફકરો - ૧", "મારો પોતાનો પ્રશ્ન (Custom)"],
        "વ્યાકરણ (૨૦ ગુણ)": ["૧. વ્યાકરણ સેટ - ૧", "મારો પોતાનો પ્રશ્ન (Custom)"]
    }
    try:
        df = pd.read_csv(url)
        q_dict = {"સંપૂર્ણ પેપર (૧૦૦ ગુણ)": ["૧. આખું TAT મેઈન્સ પેપર (તમામ પ્રશ્નો)", "મારો પોતાનો પ્રશ્ન (Custom)"]}
        for col in df.columns:
            cat = str(col).strip()
            questions = df[col].dropna().astype(str).str.strip().tolist()
            numbered_questions = [f"{i+1}. {q}" if q != "મારો પોતાનો પ્રશ્ન (Custom)" else q for i, q in enumerate(questions)]
            q_dict[cat] = numbered_questions
        for cat in q_dict:
            if "મારો પોતાનો પ્રશ્ન (Custom)" not in q_dict[cat]: q_dict[cat].append("મારો પોતાનો પ્રશ્ન (Custom)")
        return q_dict
    except: return fallback_questions

questions_dict = load_questions(GOOGLE_SHEET_CSV_URL)

# -----------------------------------------------------
# ૪. સ્ટેટ મેનેજમેન્ટ
# -----------------------------------------------------
if 'checking_result' not in st.session_state: st.session_state['checking_result'] = None

# -----------------------------------------------------
# પ્રીમિયમ ગ્રે થીમ અને લાર્જ ફોન્ટ ઈન્ટરફેસ (CSS)
# -----------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Mukta+Vaani:wght@400;600;700;800&display=swap'); 
    
    /* Global Typography */
    * { 
        font-family: 'Inter', 'Mukta Vaani', sans-serif !important; 
        font-size: 17px !important;
    }
    
    /* App Base Layout - Charcoal Grey Palette */
    .stApp {
        background-color: #1e2026;
        color: #e3e4e8;
    }
    
    /* Headings adjustments */
    .tat-title { 
        color: #f1f2f5; 
        text-align: center; 
        font-size: 34px !important; 
        font-weight: 800; 
        margin-bottom: 25px;
        letter-spacing: -0.01em;
    }
    
    /* Form Labels sizing overrides */
    label p {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #b2b5be !important;
    }
    
    /* Input element text control */
    input, select, textarea {
        font-size: 17px !important;
    }
    
    /* Question Box Custom Container - Slate Grey Tone */
    .question-box { 
        background-color: #262933; 
        border-left: 5px solid #707585; 
        border-top: 1px solid #383c4a;
        border-right: 1px solid #383c4a;
        border-bottom: 1px solid #383c4a;
        padding: 20px; 
        border-radius: 10px; 
        font-size: 19px !important; 
        color: #f1f2f5;
        margin-bottom: 20px; 
    }
    
    /* Structural custom borders */
    hr {
        border-color: #383c4a !important;
    }
    
    /* Button Text Enlargement */
    button p {
        font-size: 18px !important;
        font-weight: 600 !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# ૫. HTML રિપોર્ટ બનાવવાનું ફંક્શન
# -----------------------------------------------------
def create_html_report(text):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Gyan Academy Result</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; color: #111; background-color: #fff; }}
            h2 {{ color: #4f8ef7; text-align: center; border-bottom: 2px solid #4f8ef7; padding-bottom: 10px; margin-bottom: 20px; }}
            .content {{ white-space: pre-wrap; font-size: 16px; }}
        </style>
    </head>
    <body>
        <h2>Gyan Academy - TAT Mains Result</h2>
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

st.markdown("<div class='tat-title'>🎓 Gyan Academy - TAT પેપર ચેકિંગ</div>", unsafe_allow_html=True)

# Content Configuration Segment
category = st.selectbox("વિભાગ:", list(questions_dict.keys()))
selected_display = st.selectbox("વિષય/પ્રશ્ન પસંદ કરો:", questions_dict[category])

actual_q = re.sub(r'^\d+\. ', '', selected_display) if selected_display != "મારો પોતાનો પ્રશ્ન (Custom)" else ""
if actual_q: 
    st.markdown(f"<div class='question-box'><strong>પસંદ કરેલ પ્રશ્ન:</strong><br>{actual_q}</div>", unsafe_allow_html=True)
    
final_question_to_check = actual_q if actual_q else st.text_area("તમારો પ્રશ્ન:")

uploaded_files = st.file_uploader("PDF અથવા ફોટા પસંદ કરો (આખું પેપર હોય તો બધી ફાઈલો સિલેક્ટ કરો)", type=["jpg", "jpeg", "png", "pdf"], accept_multiple_files=True)

if st.button("પેપર ચેક કરો 🚀", type="primary", use_container_width=True):
    if not uploaded_files:
        st.warning("⚠️ ફાઈલ અપલોડ કરો.")
    else:
        with st.spinner("⏳ પેપરનું ડીપ ચેકિંગ ચાલુ છે..."):
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
                    ૪. ચર્ચાપત્ર (૨ પ્રશ્નો, કુલ ૨૦ ગુણ): દરેકના આશરે ૨૦૦ શબ્દો. પ્રત્યેકમાં મહત્તમ ૬ ગુણ. હકારાત્મક: ફોર્મેટ(૨), તટસ્થ રજૂઆત(૩), સૂચનો(૩), ભાષા(૨). નકારાત્મક: ફોર્મેટ ભૂલ(-૧ પ્રતિ ભૂલ).
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
                    ✅ હકારાત્મક ગુણ: ફોર્મેટ (કાલ્પનિક સરનામું, તંત્રીશ્રી, વિષય, સંબોધન) (૨ ગુણ), તટસ્થ રજૂઆત (૩ ગુણ), રચનાત્મક સૂચનો (૩ ગુણ), ઔપચારિક ભાષા (૨ ગુણ).
                    ❌ નકારાત્મક ગુણ: ફોર્મેટ ભૂલ (-૧ ગુણ પ્રતિ ભૂલ), અંગત/ઉગ્ર ભાષા (-૧.૫ ગુણ).
                    """
                elif category == "પત્ર લેખન":
                    total_marks = 10
                    max_marks_allowed = 6
                    expected_words = "આશરે ૧૦૦ શબ્દો"
                    category_rules = """
                    ✅ હકારાત્મક ગુણ: સત્તાવાર ફોર્મેટ (૩ ગુણ), સચોટ વિષયવસ્તુ/To the point (૪ ગુણ), સત્તાવાર શબ્દાવલિ (૩ ગુણ).
                    ❌ નકારાત્મક ગુણ: માળખાકીય ભૂલો (-૧ થી -૨ ગુણ), અસ્પષ્ટતા (-૧.૫ થી -૨ ગુણ), બિનઔપચારિક ભાષા (-૧ ગુણ).
                    """
                elif category == "સંક્ષેપીકરણ":
                    total_marks = 10
                    max_marks_allowed = 5
                    expected_words = "આપેલ ગદ્યમાંથી આશરે ૧/૩ (ત્રીજો) ભાગ"
                    category_rules = """
                    ✅ હકારાત્મક ગુણ: યોગ્ય શીર્ષક (૨ ગુણ), મૂળ વિચારની જાળવણી (૩ ગુણ), મૌલિકતા/પોતાના શબ્દોમાં (૩ ગુણ), લંબાઈ અને શુદ્ધિ (૨ ગુણ).
                    ❌ નકારાત્મક ગુણ: શીર્ષકનો અભાવ (-૨ ગુણ), કોપી-પેસ્ટ (-૨ થી -૩ ગુણ), અર્થનો અનર્થ (-૧.૫ ગુણ).
                    """
                else: # વ્યાકરણ
                    total_marks = 20
                    max_marks_allowed = 20
                    expected_words = "शબ્દમર્યાદા લાગુ પડતી નથી (૨૦ પ્રશ્નોના ટૂંકા જવાબો)"
                    category_rules = """
                    ✅ નિયમ: વ્યાકરણના ૧૦ અલગ-અલગ ટોપિક છે (રૂઢિપ્રયોગ, કહેવતો, સમાસ, છંદ, અલંકાર, શબ્દસમૂહ, જોડણી, લેખનશુદ્ધિ, સંધિ, વાક્ય રચના). દરેક ટોપિકમાંથી ફરજિયાત ૨ પ્રશ્નો પૂછાયા હશે, એમ કુલ ૨૦ પ્રશ્નો હશે. દરેક પ્રશ્નનો ૧ ગુણ છે. (કુલ ૨૦ ગુણ).
                    ✅ હકારાત્મક ગુણ: જો જવાબ વ્યાકરણની દૃષ્ટિએ અને જોડણીની દૃષ્ટિએ સંપૂર્ણ સાચો હોય તો પૂરો ૧ ગુણ આપવો.
                    ❌ નકારાત્મક ગુણ: જો જવાબ ખોટો હોય, અથવા જવાબ સાચો હોય પણ તેમાં જોડણીની સહેજ પણ ભૂલ હોય, તો સીધો ૦ (ઝીરો) ગુણ આપવો. કોઈપણ પ્રશ્નમાં અડધો (૦.૫) ગુણ આપવો જ નહીં.
                    """

                prompt = f"""
                તમે Gyan Academy ના અત્યંત હોશિયાર, કડક અને સચોટ TAT 2026 મેઈન્સ (ગુજરાતી વર્ણનાત્મક) ના પેપર ચેકર છો. 
                વિદ્યાર્થીએ '{category}' વિભાગમાં '{final_question_to_check}' વિષય પર જવાબ લખ્યો છે.
                
                તમારો જવાબ હંમેશા: "જય જ્ઞાન એકેડમી અને જય સરદાર જય પાટીદાર" થી જ શરૂ કરો. ત્યારબાદ લખો: "તમારા જવાબનું સચોટ અને વિસ્તૃત મૂલ્યાંકન નીચે મુજબ છે:"

                📏 વિભાગ અને માર્કિંગના કડક નિયમો:
                - આ પ્રશ્ન કુલ {total_marks} ગુણનો છે.
                - શબ્દમર્યાદા: {expected_words} હોવી જોઈએ.
                - સૌથી કડક નિયમ (આંતરિક - રિઝલ્ટમાં ન લખવો): ગમે તેટલો સારો જવાબ હોય, પણ દર્શાવેલ મહત્તમ લિમિટ ({max_marks_allowed}) થી વધુ ગુણ આપવા જ નહીં. આ લિમિટ વિદ્યાર્થીને કહેવાની નથી, રિઝલ્ટમાં ક્યાંય 'તમને મહત્તમ આટલા જ મળી શકે' એવું દર્શાવવું નહીં. માત્ર '{total_marks} માંથી મેળવેલ ગુણ' જ દર્શાવવા.

                {category_rules}

                ⚠️ ભાષા, મૌલિકતા અને નકારાત્મક માર્કિંગ (Negative Marking):
                - અંગ્રેજી શબ્દોનો નિષેધ: લખાણમાં અંગ્રેજી મૂળાક્ષરો (A-Z) નો પ્રયોગ સદંતર ટાળવો. જો એવો કોઈ શબ્દ હોય જેનું ગુજરાતી શક્ય જ ન હોય, તો તેનો ઉચ્ચાર ફરજિયાત ગુજરાતી લિપિમાં જ લખેલો હોવો જોઈએ (દા.ત. ઇન્ટરનેટ). જો લખાણમાં અંગ્રેજી અક્ષરો દેખાય તો માર્ક કાપવા અને સલાહમાં ટકોર કરવી.
                - મૌલિકતા: ગોખેલું કે ચીલાચાલુ લખાણ હોય તો માર્ક કાપવા, લખાણ મૌલિક અને હકારાત્મક હોવું જોઈએ.
                - દર ૩ જોડણી કે વાક્યરચનાની ભૂલ પર -૦.૫ ગુણ કાપવા.
                - પત્ર/ચર્ચાપત્રમાં જો વિદ્યાર્થીએ સાચું નામ (દા.ત. ધવલ, પટેલ, વિસનગર) લખ્યું હોય તો ઓળખ છતી કરવા બદલ સીધા -૨ ગુણ કાપવા.

                મૂલ્યાંકન નીચેના ૫ વિભાગમાં જ સુંદર રીતે આપવું:

                ### ૧. અંદાજિત શબ્દ સંખ્યા અને એનાલિસિસ: 
                (શબ્દો ગણીને જણાવો. શબ્દમર્યાદા જળવાઈ છે કે નહીં તેનું કડક વિશ્લેષણ કરો.)

                ### ૨. ક્યાં માર્કસ કપાયા અને શા માટે? (Errors Analysis): 
                (ઉપરના નિયમો મુજબ ક્યાં ભૂલ થઈ છે તે જણાવો. જો અંગ્રેજી શબ્દો વાપર્યા હોય કે મૌલિકતાનો અભાવ હોય તો ખાસ જણાવવું.)

                ### ૩. વિભાગવાર માર્કિંગ અને મેળવેલ ગુણ (Out of {total_marks}): 
                (એક સુંદર ટેબલ બનાવો. તેમાં માત્ર 'કુલ ગુણ' અને 'મેળવેલ ગુણ' જ દર્શાવવા. 'મહત્તમ આપી શકાય તેવા ગુણ' એવો કોઈ ઉલ્લેખ ભૂલથી પણ કરવો નહીં. સંપૂર્ણ પેપર હોય તો 100 ગુણની માર્કશીટ બનાવવી.)

                ### ૪. ભૂલોનું લિસ્ટ (સચોટ ચેકિંગ): 
                (જોડણી, વાક્યરચના, વિરામચિહ્નો, અંગ્રેજી શબ્દો અને ફોર્મેટની તમામ ભૂલો અહીં પોઈન્ટ્સમાં દર્શાવો.)

                ### ૫. વિસ્તૃત સલાહ અને માર્ગદર્શન (Expert Advice): 
                (અહીં અત્યંત ડીપમાં માર્ગદર્શન આપો. 
                ફરજિયાત આ વાક્યનો પ્રયોગ કરો: "જો તમે આવું લખ્યું હોત અને આ [X, Y, Z ચોક્કસ મુદ્દાઓ અને વિષયવસ્તુ] ઉમેર્યા હોત, તો તમારા માર્ક ચોક્કસ વધારે આવત." 
                વિદ્યાર્થીને સચોટ ટોપિક્સ આપો કે त्याने પોતાના જવાબમાં કઈ માહિતી લેવી જોઈતી હતી. 
                સંદર્ભ માટે માત્ર અને માત્ર સરકારી પ્રમાણભૂત સ્ત્રોતો જેવા કે: ગુજરાત પાક્ષિક, GCERT ના પુસ્તકો, ભાષા નિયામકની કચેરીના પ્રકાશનો, અને જીવન શિક્ષણ મેગેઝીન જ સૂચવવા.)
                """
                
                contents = [prompt]
                for file in uploaded_files:
                    if file.type == "application/pdf": contents.append(types.Part.from_bytes(data=file.read(), mime_type="application/pdf"))
                    else: contents.append(Image.open(file))
                
                response = client.models.generate_content(model=BEST_MODEL, contents=contents, config=types.GenerateContentConfig(temperature=0.0))
                st.session_state['checking_result'] = response.text
                st.rerun()
            except Exception as e: st.error(f"❌ ભૂલ: {e}")

# રિઝલ્ટ અને ડાઉનલોડ બટન
if st.session_state['checking_result']:
    st.markdown("<hr>", unsafe_allow_html=True)
    st.success("✅ ચેકિંગ પૂર્ણ!")
    st.markdown(st.session_state['checking_result'])
    
    # HTML રિપોર્ટ ડાઉનલોડ બટન
    report_data = create_html_report(st.session_state['checking_result'])
    st.download_button(
        label="📥 રિઝલ્ટ ડાઉનલોડ કરો",
        data=report_data,
        file_name="Gyan_Academy_Result.html",
        mime="text/html",
        use_container_width=True
    )
