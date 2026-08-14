import streamlit as st
import json
import math as m

st.set_page_config(page_title="AI Readiness Assessment 2026", layout="wide", page_icon="🤖") 

# Connection: works both in Snowflake (get_active_session) and Streamlit Community Cloud (snowflake-connector-python)
_USE_SNOWPARK = False
_session = None
_connector_conn = None

try:
    from snowflake.snowpark.context import get_active_session
    _session = get_active_session()
    _USE_SNOWPARK = True
except Exception:
    import snowflake.connector

    @st.cache_resource
    def _init_connector():
        cfg = st.secrets["connections"]["snowflake"]
        return snowflake.connector.connect(
            account=cfg["account"],
            user=cfg["user"],
            password=cfg["password"],
            role=cfg.get("role", ""),
            warehouse=cfg.get("warehouse", ""),
            database=cfg.get("database", ""),
            schema=cfg.get("schema", ""),
        )

    _connector_conn = _init_connector()


def run_sql(query, params=None):
    """Execute SQL and return list of dicts. Works in both environments."""
    if _USE_SNOWPARK:
        if params:
            result = _session.sql(query, params=params).collect()
        else:
            result = _session.sql(query).collect()
        return [row.as_dict() if hasattr(row, 'as_dict') else dict(row) for row in result]
    else:
        cur = _connector_conn.cursor()
        try:
            if params:
                cur.execute(query.replace("?", "%s"), params)
            else:
                cur.execute(query)
            if cur.description:
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, row)) for row in cur.fetchall()]
            return []
        finally:
            cur.close()

# -- Header image --
import base64
import pathlib

# Load background images as base64
_header_img_path = pathlib.Path(__file__).parent / "Picture1.png"
_bg_img_path = pathlib.Path(__file__).parent / "Picture2.png"
if _header_img_path.exists():
    _header_b64 = base64.b64encode(_header_img_path.read_bytes()).decode()
else:
    _header_b64 = ""
if _bg_img_path.exists():
    _bg_b64 = base64.b64encode(_bg_img_path.read_bytes()).decode()
else:
    _bg_b64 = ""

# -- Custom CSS --
_header_bg_css = f'background: #000000 url("data:image/png;base64,{_header_b64}") right center/contain no-repeat;' if _header_b64 else 'background: #000000;'
_page_bg_css = f'background: #1a1a2e url("data:image/png;base64,{_bg_b64}") top center/cover no-repeat fixed;' if _bg_b64 else 'background: #1a1a2e;'
st.markdown("""
<style>
    .stApp { background: #000000; }
    [data-testid="stHeader"] { background: #000000; }
    .main .block-container { padding-top: 0; }
    /* Override Streamlit text colors for dark background */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp div { color: #ffffff; }
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: #ffffff; }
    .stApp .stMarkdown p { color: #e0e0e0; }
    .stApp [data-testid="stWidgetLabel"] label { color: #ffffff !important; }
    .stApp .stSelectbox label, .stApp .stTextInput label { color: #ffffff !important; }
    .stApp .stRadio label { color: #e0e0e0 !important; }
    .stApp .stRadio [data-testid="stMarkdownContainer"] p { color: #e0e0e0 !important; }
    hr { border-color: rgba(255,255,255,0.15) !important; }
    .quiz-title {
        font-size: 96px; font-weight: 900; color: #7ED957 !important; margin: 0 0 14px 0;
        text-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .quiz-subtitle {
        font-size: 19px; color: #7ED957 !important; margin: 0; line-height: 1.6;
    }
    .section-label {
        font-size: 13px; font-weight: 700; color: #7ED957 !important; text-transform: uppercase;
        letter-spacing: 1.5px; margin-bottom: 8px; margin-top: 16px;
    }
    .question-card {
        background: transparent; border-radius: 14px; padding: 24px;
        border: 1px solid rgba(255,255,255,0.1); margin-bottom: 16px;
    }
    .question-card:hover {
        border-color: rgba(126, 217, 87, 0.3);
    }
    .question-num {
        display: inline-block; background: #7ED957; color: #000000;
        width: 28px; height: 28px; border-radius: 50%; text-align: center;
        line-height: 28px; font-size: 13px; font-weight: 700; margin-right: 10px;
    }
    .question-text {
        font-size: 15px; font-weight: 600; color: #ffffff; display: inline;
    }
    .dimension-tag {
        display: inline-block; font-size: 10px; font-weight: 600;
        padding: 2px 8px; border-radius: 10px; margin-left: 8px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .result-hero {
        background: rgba(0,0,0,0.4); backdrop-filter: blur(10px);
        border-radius: 24px; padding: 48px; text-align: center;
        border: 1px solid rgba(126, 217, 87, 0.3); margin-bottom: 32px;
    }
    .score-card {
        border-radius: 16px; padding: 24px; text-align: center;
        background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1);
        transition: transform 0.2s ease;
    }
    .score-card:hover {
        transform: translateY(-2px);
    }
    .insight-card {
        background: rgba(0,0,0,0.3); border-radius: 12px; padding: 16px 20px;
        border-left: 4px solid #7ED957; margin-bottom: 12px;
    }
    .cta-card {
        background: rgba(0,0,0,0.4); backdrop-filter: blur(10px);
        border-radius: 20px; padding: 32px;
        border: 1px solid rgba(126, 217, 87, 0.3); text-align: center;
    }
    .respondent-card {
        background: rgba(0,0,0,0.3); border-radius: 16px; padding: 24px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .ai-card {
        background: rgba(0,0,0,0.4); backdrop-filter: blur(10px);
        border-radius: 20px; padding: 28px;
        border: 1px solid rgba(126, 217, 87, 0.3); margin-top: 16px;
    }
    .progress-bar-container {
        background: rgba(0,0,0,0.3); border-radius: 12px; padding: 16px 24px;
        border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;
    }
    .peer-badge {
        background: rgba(0,0,0,0.4);
        border-radius: 16px; padding: 20px 28px;
        border: 1px solid rgba(126, 217, 87, 0.3); text-align: center;
        margin: 16px 0;
    }
    [data-testid="stMetric"] {
        background: rgba(0,0,0,0.3);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px; padding: 1rem;
    }
    [data-testid="stMetric"] label { color: #7ED957 !important; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { color: #ffffff !important; }
    /* Primary button styling */
    .stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"] {
        background-color: #7ED957 !important;
        color: #000000 !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover {
        background-color: #6bc648 !important;
    }
    /* Download button styling */
    .stDownloadButton > button {
        background-color: #7ED957 !important;
        color: #000000 !important;
        border: none !important;
        font-weight: 700 !important;
    }
    .stDownloadButton > button:hover {
        background-color: #6bc648 !important;
    }
    /* Print styles for PDF export */
    @media print {
        /* Hide Streamlit UI chrome */
        [data-testid="stHeader"], [data-testid="stSidebar"],
        [data-testid="stToolbar"], .stDeployButton,
        .stDownloadButton, .print-hide,
        iframe, footer, header, .stButton,
        [data-testid="stDecoration"], [data-testid="stStatusWidget"] { 
            display: none !important; 
        }
        /* Page setup */
        @page { margin: 1.5cm; size: A4; }
        body, .stApp { 
            background: white !important; 
            color: #1e293b !important;
        }
        /* Hide URL in header/footer of printed page */
        @page { margin-top: 1.5cm; margin-bottom: 1.5cm; }
        @page :first { margin-top: 1.5cm; }
        .block-container { 
            padding: 0 !important; 
            max-width: 100% !important;
            margin: 0 !important;
        }
        /* Prevent page breaks inside cards */
        .result-hero, .score-card, .insight-card, .ai-card,
        .cta-card, .respondent-card, .peer-badge,
        [data-testid="column"] {
            break-inside: avoid !important;
            page-break-inside: avoid !important;
        }
        /* Fix dark backgrounds for print */
        .result-hero {
            background: #f0fdf4 !important;
            border: 2px solid #86efac !important;
        }
        .score-card {
            background: #f8fafc !important;
            border: 1px solid #e2e8f0 !important;
        }
        .insight-card {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-left: 4px solid #10b981 !important;
        }
        .ai-card {
            background: #f0fdf4 !important;
            border: 1px solid #86efac !important;
        }
        .cta-card {
            background: #f0f9ff !important;
            border: 1px solid #bfdbfe !important;
        }
        .respondent-card {
            background: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
        }
        .peer-badge {
            background: #ecfdf5 !important;
            border: 1px solid #86efac !important;
        }
        /* Make all text dark for readability */
        p, span, div, h1, h2, h3, h4, label {
            color: #1e293b !important;
        }
        /* Preserve colors in charts and badges */
        svg { print-color-adjust: exact !important; -webkit-print-color-adjust: exact !important; }
        * { 
            color-adjust: exact !important; 
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        /* Clean spacing */
        .stMarkdown { margin-bottom: 8px !important; }
        hr { border-color: #e2e8f0 !important; }
    }
</style>
""", unsafe_allow_html=True)

# -- Session State --
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'responses' not in st.session_state:
    st.session_state.responses = {}

# -- Header --
_header3_path = pathlib.Path(__file__).parent / "Picture3.png"
st.image(str(_header3_path), use_container_width=True)

if not st.session_state.quiz_submitted:

    # ============================================================
    # SECTION 1: CONTACT FORM
    # ============================================================
    st.markdown('<p class="section-label">👤 About You</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", placeholder="Jane Smith")
        email = st.text_input("Email", placeholder="jane@company.com")
        company = st.text_input("Company / Organization", placeholder="Acme Corp")
    with col2:
        role = st.selectbox("Your Role", [
            "A) Set strategy / own budget",
            "B) Lead a function that would implement AI",
            "C) Practitioner / manager who'd use AI",
            "D) Exploring, not a formal owner"
        ], index=None, placeholder="Select your role...")
        industry = st.selectbox("Industry", [
            "A) Financial Services / Insurance",
            "B) Manufacturing / Industrial / Logistics",
            "C) Retail / Consumer / F&B",
            "D) Public Sector / Healthcare / Other regulated",
            "E) Others"
        ], index=None, placeholder="Select your industry...")

    st.markdown("---")

    # ============================================================
    # SECTION 2: SCORED QUIZ (10 Questions)
    # ============================================================
    st.markdown('<p class="section-label">📊 AI Maturity Assessment</p>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(0,0,0,0.3); border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);">
        <span style="font-size: 14px; color: #e0e0e0;">💡 Answer honestly based on where your organisation is <em>today</em>, not where you aspire to be.</span>
    </div>
    """, unsafe_allow_html=True)

    questions = [
        {
            "num": 1, "icon": "🎯",
            "text": "How would you describe your organisation's current relationship with AI?",
            "options": [
                "A) Still evaluating",
                "B) A few experiments / POCs",
                "C) Production use case + dedicated team/budget",
                "D) Production across multiple functions, part of strategy"
            ],
            "dimension": "Strategy & Leadership",
            "dim_color": "#059669", "dim_bg": "#ecfdf5"
        },
        {
            "num": 2, "icon": "🏛️",
            "text": "How is AI ownership structured within your organisation?",
            "options": [
                "A) No clear owner",
                "B) Individual champions, uncoordinated",
                "C) Dedicated team, siloed by department",
                "D) Centralised AI CoE, enterprise-wide"
            ],
            "dimension": "Governance & Talent",
            "dim_color": "#0ea5e9", "dim_bg": "#f0f9ff"
        },
        {
            "num": 3, "icon": "🚀",
            "text": "How many AI use cases does your organisation currently have live in production (not pilots)?",
            "options": [
                "A) None",
                "B) 1",
                "C) 2–4, mostly one department",
                "D) 5+, multiple departments"
            ],
            "dimension": "Data & Technology",
            "dim_color": "#10b981", "dim_bg": "#ecfdf5"
        },
        {
            "num": 4, "icon": "🗄️",
            "text": "How would you rate your organisation's data readiness?",
            "options": [
                "A) Scattered / hard to access",
                "B) Usable but depends who you ask",
                "C) Reasonably governed for core domains",
                "D) Modern, governed platform"
            ],
            "dimension": "Data & Technology",
            "dim_color": "#10b981", "dim_bg": "#ecfdf5"
        },
        {
            "num": 5, "icon": "🛡️",
            "text": "Do you have a formal AI governance / risk framework?",
            "options": [
                "A) None",
                "B) Informal, undocumented",
                "C) Documented, not enforced",
                "D) Mature, enforced"
            ],
            "dimension": "Governance & Talent",
            "dim_color": "#0ea5e9", "dim_bg": "#f0f9ff"
        },
        {
            "num": 6, "icon": "👥",
            "text": "Does your organisation have in-house skills to build/deploy/maintain AI without external help?",
            "options": [
                "A) No dedicated talent",
                "B) Small team, stretched thin",
                "C) Dedicated team, skill gaps",
                "D) Fully staffed, specialised"
            ],
            "dimension": "Governance & Talent",
            "dim_color": "#0ea5e9", "dim_bg": "#f0f9ff"
        },
        {
            "num": 7, "icon": "📈",
            "text": "How does your organisation measure the success or ROI of AI initiatives?",
            "options": [
                "A) Don't formally measure",
                "B) Track usage, not impact",
                "C) Measure impact for some initiatives",
                "D) Consistent ROI framework across initiatives"
            ],
            "dimension": "Strategy & Leadership",
            "dim_color": "#059669", "dim_bg": "#ecfdf5"
        },
        {
            "num": 8, "icon": "🚧",
            "text": "What's the single biggest thing currently holding your AI initiatives back?",
            "options": [
                "A) Unclear use cases",
                "B) Data quality / access",
                "C) Lack of skilled people",
                "D) Governance / risk / buy-in",
                "E) Other (specify below)"
            ],
            "dimension": "Pain Point",
            "dim_color": "#f59e0b", "dim_bg": "#fffbeb"
        },
        {
            "num": 9, "icon": "💰",
            "text": "What's your appetite/timeline for new AI investment in the next 12 months?",
            "options": [
                "A) No budget / timeline",
                "B) Early planning",
                "C) Budget approved, scoping",
                "D) Actively executing, seeking partners"
            ],
            "dimension": "Lead Intent",
            "dim_color": "#ec4899", "dim_bg": "#fdf2f8"
        },
        {
            "num": 10, "icon": "🤝",
            "text": "If you could get one thing from a conversation with an AI consulting partner today, what would it be?",
            "options": [
                "A) Help identifying use cases",
                "B) Objective readiness assessment",
                "C) Help running a pilot",
                "D) Help scaling / governing existing AI"
            ],
            "dimension": "Desired Engagement",
            "dim_color": "#8b5cf6", "dim_bg": "#faf5ff"
        },
    ]

    responses = {}
    answered_count = 0
    for q in questions:
        st.markdown(f"""
        <div class="question-card">
            <span class="question-num">{q['num']}</span>
            <span style="margin-right: 6px;">{q['icon']}</span>
            <span class="question-text">{q['text']}</span>
            <span class="dimension-tag" style="color:{q['dim_color']};background:{q['dim_bg']};">{q['dimension']}</span>
        </div>
        """, unsafe_allow_html=True)
        responses[f"q{q['num']}"] = st.radio(
            f"Q{q['num']}", q['options'], key=f"q{q['num']}", label_visibility="collapsed", index=None
        )
        if responses[f"q{q['num']}"] is not None:
            answered_count += 1
        # Show "Please specify" immediately after Q8 if "Other" is selected
        if q['num'] == 8 and (responses.get("q8") or "").startswith("E)"):
            responses["q8_other"] = st.text_input("Please specify:", key="q8_other_text")

    # Progress bar
    progress_pct = int((answered_count / 10) * 100)
    st.markdown(f"""
    <div class="progress-bar-container">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <span style="font-size: 13px; font-weight: 600; color: #7ED957;">📝 Progress</span>
        <span style="font-size: 13px; font-weight: 700; color: #7ED957;">{answered_count}/10 questions answered</span>
        </div>
        <div style="background: #e2e8f0; border-radius: 8px; height: 10px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #10b981, #059669); width: {progress_pct}%; height: 100%; border-radius: 8px; transition: width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Submit
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 12px;">
            <span style="font-size: 13px; color: #7ED957;">🔒 Your responses are confidential</span>
            <p style="font-size: 11px; color: #7ED957; opacity: 0.8; margin: 8px 0 0 0; line-height: 1.5; max-width: 500px; display: inline-block;">
                By submitting this survey, you consent to the use of your information to assess your organisation's AI readiness and to support follow-up activities, engagement, and the provision of relevant Deloitte services. To view our Privacy statement, please visit <a href="https://www.deloitte.com/southeast-asia/en/legal/privacy.html?icid=bottom_privacy" target="_blank" style="color: #7ED957;">Deloitte Privacy</a>.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Submit Assessment", type="primary", use_container_width=True):
            # Validation: check required fields and all questions answered
            if not name or not email:
                st.error("⚠️ Please provide your name and email.")
            elif answered_count < 10:
                unanswered = [str(i+1) for i in range(10) if responses.get(f"q{i+1}") is None]
                st.error(f"⚠️ Please answer all questions. Missing: Q{', Q'.join(unanswered)}")
            else:
                st.session_state.responses = {
                    "name": name,
                    "email": email,
                    "company": company,
                    "role": role,
                    "industry": industry,
                    **responses
                }
                st.session_state.quiz_submitted = True
                st.rerun()

# ============================================================
# RESULTS PAGE
# ============================================================
else:
    # Scroll to top when results load using CSS trick
    st.markdown("""
    <style>
        /* Force scroll to top on results page */
        [data-testid="stAppViewContainer"] {
            scroll-behavior: auto;
        }
    </style>
    <iframe src="javascript:window.parent.document.querySelector('section.main').scrollTo(0,0)" style="display:none;"></iframe>
    """, unsafe_allow_html=True)
    
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
            // Try multiple scroll targets
            var main = window.parent.document.querySelector('section.main');
            if (main) main.scrollTop = 0;
            var container = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
            if (container) container.scrollTop = 0;
            var block = window.parent.document.querySelector('.block-container');
            if (block) block.scrollIntoView({behavior: 'instant'});
            window.parent.scrollTo(0, 0);
        </script>
        """,
        height=0
    )

    r = st.session_state.responses

    # Scoring function
    def score_answer(answer):
        if not answer:
            return 0
        letter = answer[0]
        return {"A": 1, "B": 2, "C": 3, "D": 4}.get(letter, 0)

    # Calculate scores
    strategy_score = score_answer(r.get("q1", "")) + score_answer(r.get("q7", ""))
    governance_score = score_answer(r.get("q2", "")) + score_answer(r.get("q5", "")) + score_answer(r.get("q6", ""))
    data_tech_score = score_answer(r.get("q3", "")) + score_answer(r.get("q4", ""))
    lead_intent = score_answer(r.get("q9", ""))
    role_score = score_answer(r.get("role", ""))
    lead_intent_combined = lead_intent + role_score

    total_maturity = strategy_score + governance_score + data_tech_score
    max_maturity = 28
    pct = total_maturity / max_maturity * 100

    # Maturity level
    if pct < 30:
        level = "Exploring"
        level_color = "#64748b"
        level_icon = "🔍"
        level_desc = "Your organisation is in early stages of AI adoption. Focus on identifying high-value use cases and building foundational data capabilities."
    elif pct < 55:
        level = "Experimenting"
        level_color = "#f59e0b"
        level_icon = "🧪"
        level_desc = "You've started the journey with POCs or limited production. Key next step: establish governance and scale what works."
    elif pct < 80:
        level = "Scaling"
        level_color = "#0ea5e9"
        level_icon = "📈"
        level_desc = "Production AI exists with dedicated resources. Focus on cross-functional expansion, ROI measurement, and governance maturity."
    else:
        level = "Leading"
        level_color = "#10b981"
        level_icon = "🏆"
        level_desc = "AI is embedded in your strategy across functions. Focus on optimisation, advanced governance, and competitive differentiation."

    # Save to Snowflake table
    try:
        run_sql("""
            INSERT INTO AI_READINESS.PUBLIC.AI_READINESS_RESPONSES
            (NAME, EMAIL, COMPANY, ROLE, INDUSTRY, Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q8_OTHER, Q9, Q10,
             STRATEGY_SCORE, GOVERNANCE_SCORE, DATA_TECH_SCORE, TOTAL_MATURITY, MATURITY_PCT, MATURITY_LEVEL)
            SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        """, params=[
            r.get("name", ""), r.get("email", ""), r.get("company", ""),
            r.get("role", ""), r.get("industry", ""),
            r.get("q1", ""), r.get("q2", ""), r.get("q3", ""), r.get("q4", ""),
            r.get("q5", ""), r.get("q6", ""), r.get("q7", ""), r.get("q8", ""),
            r.get("q8_other", ""), r.get("q9", ""), r.get("q10", ""),
            strategy_score, governance_score, data_tech_score,
            total_maturity, pct, level
        ])
    except Exception:
        pass

    # Animated loading for Cortex (spinner)
    with st.spinner("🔍 Analysing your responses with AI..."):

        # Display results hero
        st.markdown(f"""
        <div class="result-hero" style="background: linear-gradient(135deg, rgba(126,217,87,0.08) 0%, rgba(0,0,0,0.5) 50%, rgba(126,217,87,0.05) 100%); border: 1px solid rgba(126,217,87,0.4); padding: 60px 48px;">
            <p style="font-size: 64px; margin: 0 0 8px 0; filter: drop-shadow(0 0 12px rgba(126,217,87,0.4));">{level_icon}</p>
            <p style="font-size: 12px; color: #7ED957; font-weight: 700; text-transform: uppercase; letter-spacing: 3px; margin: 0 0 12px 0;">Your AI Maturity Level</p>
            <p style="font-size: 56px; font-weight: 900; color: #7ED957; margin: 0 0 16px 0; text-shadow: 0 0 20px rgba(126,217,87,0.3);">{level}</p>
            <p style="font-size: 16px; color: rgba(255,255,255,0.8); margin: 0; max-width: 600px; display: inline-block; line-height: 1.7;">{level_desc}</p>
            <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid rgba(255,255,255,0.1);">
                <span style="font-size: 36px; font-weight: 900; color: #ffffff;">{total_maturity}</span>
                <span style="font-size: 18px; color: #94a3b8;">/{max_maturity} points</span>
                <span style="font-size: 14px; color: #7ED957; margin-left: 16px; font-weight: 600;">({pct:.0f}%)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Score breakdown
        st.markdown("### 📊 Score Breakdown")
        col1, col2, col3 = st.columns(3)

        with col1:
            strat_pct_val = int(strategy_score / 8 * 100)
            st.markdown(f"""
            <div class="score-card" style="border: 1px solid rgba(126,217,87,0.3); background: linear-gradient(180deg, rgba(126,217,87,0.05) 0%, rgba(0,0,0,0.3) 100%);">
                <div style="font-size: 32px; margin-bottom: 12px; filter: drop-shadow(0 0 8px rgba(126,217,87,0.3));">🎯</div>
                <div style="font-size: 11px; color: #7ED957; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Strategy & Leadership</div>
                <div style="font-size: 38px; font-weight: 900; color: #ffffff; margin-top: 12px;">{strategy_score}<span style="font-size: 16px; color: #94a3b8;">/8</span></div>
                <div style="margin-top: 12px; background: rgba(255,255,255,0.08); border-radius: 6px; height: 6px; overflow: hidden;">
                    <div style="background: #7ED957; width: {strat_pct_val}%; height: 100%; border-radius: 6px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            gov_pct_val = int(governance_score / 12 * 100)
            st.markdown(f"""
            <div class="score-card" style="border: 1px solid rgba(126,217,87,0.3); background: linear-gradient(180deg, rgba(126,217,87,0.05) 0%, rgba(0,0,0,0.3) 100%);">
                <div style="font-size: 32px; margin-bottom: 12px; filter: drop-shadow(0 0 8px rgba(126,217,87,0.3));">🛡️</div>
                <div style="font-size: 11px; color: #7ED957; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Governance & Talent</div>
                <div style="font-size: 38px; font-weight: 900; color: #ffffff; margin-top: 12px;">{governance_score}<span style="font-size: 16px; color: #94a3b8;">/12</span></div>
                <div style="margin-top: 12px; background: rgba(255,255,255,0.08); border-radius: 6px; height: 6px; overflow: hidden;">
                    <div style="background: #7ED957; width: {gov_pct_val}%; height: 100%; border-radius: 6px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            data_pct_val = int(data_tech_score / 8 * 100)
            st.markdown(f"""
            <div class="score-card" style="border: 1px solid rgba(126,217,87,0.3); background: linear-gradient(180deg, rgba(126,217,87,0.05) 0%, rgba(0,0,0,0.3) 100%);">
                <div style="font-size: 32px; margin-bottom: 12px; filter: drop-shadow(0 0 8px rgba(126,217,87,0.3));">⚙️</div>
                <div style="font-size: 11px; color: #7ED957; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">Data & Technology</div>
                <div style="font-size: 38px; font-weight: 900; color: #ffffff; margin-top: 12px;">{data_tech_score}<span style="font-size: 16px; color: #94a3b8;">/8</span></div>
                <div style="margin-top: 12px; background: rgba(255,255,255,0.08); border-radius: 6px; height: 6px; overflow: hidden;">
                    <div style="background: #7ED957; width: {data_pct_val}%; height: 100%; border-radius: 6px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Radar chart (pure SVG - no external dependencies)
        st.markdown("### 🕸️ Dimension Radar")

        # Calculate percentage values for each dimension
        strat_pct = strategy_score / 8 * 100
        gov_pct = governance_score / 12 * 100
        data_pct = data_tech_score / 8 * 100

        # SVG radar chart - equilateral triangle with 3 axes
        cx, cy, radius = 200, 160, 90
        angles = [-90, 30, 150]
        axis_pts = [(cx + radius * m.cos(m.radians(a)), cy + radius * m.sin(m.radians(a))) for a in angles]
        data_pts = [(cx + radius * (v/100) * m.cos(m.radians(a)), cy + radius * (v/100) * m.sin(m.radians(a)))
                    for a, v in zip(angles, [strat_pct, gov_pct, data_pct])]

        grid_svg = ""
        for ring_pct in [25, 50, 75, 100]:
            ring_r = radius * ring_pct / 100
            pts = " ".join([f"{cx + ring_r * m.cos(m.radians(a))},{cy + ring_r * m.sin(m.radians(a))}" for a in angles])
            grid_svg += f'<polygon points="{pts}" fill="none" stroke="rgba(255,255,255,0.15)" stroke-width="1"/>'

        axes_svg = "".join([f'<line x1="{cx}" y1="{cy}" x2="{p[0]}" y2="{p[1]}" stroke="rgba(255,255,255,0.2)" stroke-width="1"/>' for p in axis_pts])
        data_polygon = " ".join([f"{p[0]},{p[1]}" for p in data_pts])

        label_offset = 30
        labels = [
            (cx, cy + (radius + label_offset) * m.sin(m.radians(-90)) - 10, "Strategy & Leadership", f"{strat_pct:.0f}%"),
            (cx + (radius + label_offset) * m.cos(m.radians(30)) + 20, cy + (radius + label_offset) * m.sin(m.radians(30)) + 16, "Governance & Talent", f"{gov_pct:.0f}%"),
            (cx + (radius + label_offset) * m.cos(m.radians(150)) - 20, cy + (radius + label_offset) * m.sin(m.radians(150)) + 16, "Data & Technology", f"{data_pct:.0f}%"),
        ]

        labels_svg = ""
        for lx, ly, name, val in labels:
            anchor = "middle"
            if "Governance" in name:
                anchor = "start"
            elif "Data" in name:
                anchor = "end"
            labels_svg += f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="12" font-weight="bold" fill="#ffffff">{name}</text>'
            labels_svg += f'<text x="{lx}" y="{ly + 16}" text-anchor="{anchor}" font-size="12" font-weight="600" fill="#7ED957">{val}</text>'

        radar_svg = f"""
        <div style="display: flex; justify-content: center; margin: 16px 0; padding: 24px; background: rgba(0,0,0,0.3); border-radius: 16px; border: 1px solid rgba(255,255,255,0.1);">
            <svg width="100%" height="320" viewBox="0 0 400 320" xmlns="http://www.w3.org/2000/svg">
                {grid_svg}
                {axes_svg}
                <polygon points="{data_polygon}" fill="rgba(126, 217, 87, 0.15)" stroke="#7ED957" stroke-width="2.5"/>
                <circle cx="{data_pts[0][0]}" cy="{data_pts[0][1]}" r="6" fill="#7ED957" style="filter: drop-shadow(0 0 6px rgba(126,217,87,0.6));"/>
                <circle cx="{data_pts[1][0]}" cy="{data_pts[1][1]}" r="6" fill="#7ED957" style="filter: drop-shadow(0 0 6px rgba(126,217,87,0.6));"/>
                <circle cx="{data_pts[2][0]}" cy="{data_pts[2][1]}" r="6" fill="#7ED957" style="filter: drop-shadow(0 0 6px rgba(126,217,87,0.6));"/>
                {labels_svg}
            </svg>
        </div>
        """
        st.markdown(radar_svg, unsafe_allow_html=True)

        # Maturity bar
        st.markdown("### 📏 Overall Maturity Score")
        st.markdown(f"""
        <div style="margin: 16px 0; background: rgba(0,0,0,0.3); border-radius: 16px; padding: 24px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span style="font-size: 14px; color: #e0e0e0; font-weight: 600;">Progress</span>
                <span style="font-size: 14px; font-weight: 700; color: #7ED957;">{total_maturity}/{max_maturity} ({pct:.0f}%)</span>
            </div>
            <div style="background: rgba(255,255,255,0.1); border-radius: 10px; height: 16px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #7ED957, #6bc648); width: {pct}%; height: 100%; border-radius: 10px; transition: width 0.5s ease;"></div>
            </div>
            <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                <span style="font-size: 11px; color: #94a3b8;">🔍 Exploring</span>
                <span style="font-size: 11px; color: #94a3b8;">🧪 Experimenting</span>
                <span style="font-size: 11px; color: #94a3b8;">📈 Scaling</span>
                <span style="font-size: 11px; color: #94a3b8;">🏆 Leading</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Peer comparison badge
        try:
            industry_val = r.get("industry", "")
            if industry_val:
                escaped_industry = industry_val.replace("'", "''")
                peer_result = run_sql(f"""
                    SELECT
                        COUNT(*) AS total_peers,
                        SUM(CASE WHEN TOTAL_MATURITY < {total_maturity} THEN 1 ELSE 0 END) AS below_you
                    FROM AI_READINESS.PUBLIC.AI_READINESS_RESPONSES
                    WHERE INDUSTRY = '{escaped_industry}'
                """)
                total_peers = peer_result[0]["TOTAL_PEERS"]
                below_you = peer_result[0]["BELOW_YOU"]
                if total_peers > 1:
                    percentile = int((below_you / (total_peers - 1)) * 100)
                    industry_short = industry_val.split(") ")[1] if ") " in industry_val else industry_val
                    st.markdown(f"""
                    <div class="peer-badge">
                        <span style="font-size: 28px;">🏅</span>
<p style="font-size: 18px; font-weight: 800; color: #7ED957; margin: 8px 0 4px 0;">You scored higher than {percentile}% of {industry_short} respondents</p>
<p style="font-size: 13px; color: #e0e0e0; margin: 0;">Based on {total_peers} responses in your industry</p>
                    </div>
                    """, unsafe_allow_html=True)
        except Exception:
            pass

        # Key insights
        st.markdown("### 💡 Key Insights")

        insights = []
        if score_answer(r.get("q1", "")) >= 3 and score_answer(r.get("q7", "")) <= 2:
            insights.append(("⚠️", "Ambition-Measurement Gap", "You rate AI maturity highly but don't formally measure ROI. Consider establishing success metrics before scaling further.", "#f59e0b"))
        if score_answer(r.get("q3", "")) >= 3 and score_answer(r.get("q5", "")) <= 2:
            insights.append(("⚠️", "Scaling Without Governance", "You have production AI but limited governance. This creates risk as you scale — prioritise a formal AI risk framework.", "#f59e0b"))
        if score_answer(r.get("q1", "")) >= 3 and score_answer(r.get("q4", "")) <= 2:
            insights.append(("⚠️", "Ambition Outrunning Data", "Your AI aspirations exceed your data foundation. Invest in data governance before adding more AI use cases.", "#f59e0b"))
        if score_answer(r.get("q2", "")) <= 1:
            insights.append(("💡", "No AI Owner", "Consider establishing an AI Center of Excellence (CoE) to coordinate efforts and avoid duplication.", "#10b981"))
        if score_answer(r.get("q6", "")) <= 2:
            insights.append(("💡", "Skill Gap", "Your team may need external support for AI initiatives. Consider advisory partnerships for build vs. buy decisions.", "#10b981"))

        if not insights:
            insights.append(("✅", "Well Balanced", "Your scores are well-balanced across dimensions. Focus on continuous improvement and staying ahead of governance requirements.", "#10b981"))

        for icon, title, desc, color in insights:
            st.markdown(f"""
            <div class="insight-card" style="border-left-color: {color};">
<div style="font-size: 14px; font-weight: 700; color: #ffffff; margin-bottom: 4px;">{icon} {title}</div>
<div style="font-size: 13px; color: #e0e0e0; line-height: 1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        # AI-powered holistic insights via Cortex Complete
        response_summary = "\n".join([
            f"Q1 - AI Relationship: {r.get('q1', 'N/A')}",
            f"Q2 - AI Ownership Structure: {r.get('q2', 'N/A')}",
            f"Q3 - Production Use Cases: {r.get('q3', 'N/A')}",
            f"Q4 - Data Readiness: {r.get('q4', 'N/A')}",
            f"Q5 - Governance Framework: {r.get('q5', 'N/A')}",
            f"Q6 - In-house AI Skills: {r.get('q6', 'N/A')}",
            f"Q7 - ROI Measurement: {r.get('q7', 'N/A')}",
            f"Q8 - Biggest Blocker: {r.get('q8', 'N/A')} {r.get('q8_other', '')}",
            f"Q9 - Investment Appetite: {r.get('q9', 'N/A')}",
            f"Q10 - Desired Engagement: {r.get('q10', 'N/A')}",
            f"Role: {r.get('role', 'N/A')}",
            f"Industry: {r.get('industry', 'N/A')}",
            f"Maturity Level: {level} ({pct:.0f}%)",
            f"Strategy and Leadership Score: {strategy_score}/8",
            f"Governance and Talent Score: {governance_score}/12",
            f"Data and Technology Score: {data_tech_score}/8",
        ])

        prompt = (
            "You are an AI readiness consultant. A user completed a 10-question AI maturity quiz. "
            "Write an analysis (100-120 words, 2 paragraphs) that: "
            "1. First paragraph: Summarize their maturity posture in context of their industry and role, "
            "and name the single biggest gap with a brief explanation of why it matters. "
            "2. Second paragraph: Provide 2-3 specific recommendations as short bullet points "
            "(one sentence each, include enough context to be actionable).\n\n"
            "Rules: Be consultative and direct. No filler or hype. Stay within 120 words.\n\n"
            f"Assessment Responses:\n{response_summary}\n\n"
            "Output plain text only."
        )

        try:
            escaped_prompt = prompt.replace("'", "''").replace("\\", "\\\\")
            sql_query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', '{escaped_prompt}') AS RESPONSE"
            ai_result = run_sql(sql_query)
            ai_insights = ai_result[0]["RESPONSE"] if ai_result else ""
            if ai_insights:
                st.session_state.ai_insights_text = ai_insights
                st.markdown("### 🤖 AI-Powered Holistic Analysis")
                st.markdown('<span style="font-size: 12px; color: #7ED957; font-weight: 600;">✨ Powered by Snowflake Cortex</span>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="ai-card">
                    <div style="font-size: 11px; color: #7ED957; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">🧠 Cortex AI Analysis</div>
                    <div style="font-size: 14px; color: #e0e0e0; line-height: 1.7;">{ai_insights}</div>
                </div>
    """, unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ AI analysis unavailable: {e}")

    # CTA based on Q10
    st.markdown("---")
    q10_answer = r.get("q10", "") or ""
    if "identifying use cases" in q10_answer:
        cta_icon = "🎯"
        cta = "We'd love to help you identify high-impact AI use cases tailored to your industry and maturity level."
    elif "readiness assessment" in q10_answer:
        cta_icon = "📋"
        cta = "Let's schedule a deeper AI readiness assessment to map your specific gaps and opportunities."
    elif "running a pilot" in q10_answer:
        cta_icon = "🚀"
        cta = "We can help you design and execute a focused AI pilot that proves value quickly."
    else:
        cta_icon = "📈"
        cta = "Let's discuss how to scale and govern your existing AI initiatives for maximum impact."

    st.markdown(f"""
    <div class="cta-card">
        <p style="font-size: 32px; margin: 0 0 8px 0;">{cta_icon}</p>
<p style="font-size: 17px; color: #ffffff; font-weight: 700; margin: 0 0 8px 0;">Recommended Next Step</p>
<p style="font-size: 15px; color: #e0e0e0; margin: 0; line-height: 1.6;">{cta}</p>
    </div>
    """, unsafe_allow_html=True)

    # Respondent summary
    st.markdown("---")
    st.markdown("### 👤 Respondent Details")
    st.markdown(f"""
    <div class="respondent-card">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
<div><span style="font-size: 12px; color: #7ED957; font-weight: 600; text-transform: uppercase;">Name</span><br><span style="font-size: 14px; color: #ffffff;">{r.get('name', '')}</span></div>
<div><span style="font-size: 12px; color: #7ED957; font-weight: 600; text-transform: uppercase;">Email</span><br><span style="font-size: 14px; color: #ffffff;">{r.get('email', '')}</span></div>
<div><span style="font-size: 12px; color: #7ED957; font-weight: 600; text-transform: uppercase;">Company</span><br><span style="font-size: 14px; color: #ffffff;">{r.get('company', '')}</span></div>
<div><span style="font-size: 12px; color: #7ED957; font-weight: 600; text-transform: uppercase;">Role</span><br><span style="font-size: 14px; color: #ffffff;">{r.get('role', '')}</span></div>
<div><span style="font-size: 12px; color: #7ED957; font-weight: 600; text-transform: uppercase;">Industry</span><br><span style="font-size: 14px; color: #ffffff;">{r.get('industry', '')}</span></div>
<div><span style="font-size: 12px; color: #7ED957; font-weight: 600; text-transform: uppercase;">Biggest Blocker</span><br><span style="font-size: 14px; color: #ffffff;">{r.get('q8', '')} {r.get('q8_other', '')}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- Export Results ---
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; margin-bottom: 16px;">
        <p style="font-size: 18px; font-weight: 700; color: #ffffff; margin: 0 0 4px 0;">📥 Export Your Results</p>
        <p style="font-size: 13px; color: #94a3b8; margin: 0;">Save your assessment for future reference or share with your team</p>
    </div>
    """, unsafe_allow_html=True)

    import streamlit.components.v1 as components
    components.html(
        """
        <div style="text-align: center;">
            <button onclick="window.parent.print()" style="
                padding: 10px 28px;
                background-color: #7ED957;
                color: #000000;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
                cursor: pointer;
            ">📑 Save as PDF</button>
            <p style="font-size: 11px; color: #64748b; margin-top: 10px;">
                Tip: In print dialog, uncheck "Headers and footers" to remove the URL.
            </p>
        </div>
        """,
        height=80
    )
