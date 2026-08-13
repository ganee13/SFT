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

# -- Custom CSS --
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #ffffff 0%, #f8fafc 50%, #f0f9ff 100%); }
    [data-testid="stHeader"] { background: transparent; }
    .quiz-header {
        background: linear-gradient(135deg, #10b981 0%, #059669 30%, #34d399 60%, #6ee7b7 100%);
        background-size: 300% 300%;
        animation: gradientShift 8s ease infinite;
        border-radius: 24px; padding: 56px 40px; text-align: center;
        border: none; margin-bottom: 32px;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.25);
        position: relative; overflow: hidden;
    }
    .quiz-header::before {
        content: '';
        position: absolute; top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
        animation: shimmer 6s linear infinite;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes shimmer {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .quiz-title {
        font-size: 68px; font-weight: 900; color: #ffffff; margin: 0 0 14px 0;
        text-shadow: 0 2px 8px rgba(0,0,0,0.15);
        position: relative;
    }
    .quiz-subtitle {
        font-size: 19px; color: rgba(255,255,255,0.9); margin: 0; line-height: 1.6;
        position: relative;
    }
    .section-label {
        font-size: 13px; font-weight: 700; color: #059669; text-transform: uppercase;
        letter-spacing: 1.5px; margin-bottom: 8px; margin-top: 16px;
    }
    .question-card {
        background: white; border-radius: 14px; padding: 24px;
        border: 1px solid #e2e8f0; margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        transition: box-shadow 0.2s ease;
    }
    .question-card:hover {
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.1);
    }
    .question-num {
        display: inline-block; background: #059669; color: white;
        width: 28px; height: 28px; border-radius: 50%; text-align: center;
        line-height: 28px; font-size: 13px; font-weight: 700; margin-right: 10px;
    }
    .question-text {
        font-size: 15px; font-weight: 600; color: #1e293b; display: inline;
    }
    .dimension-tag {
        display: inline-block; font-size: 10px; font-weight: 600;
        padding: 2px 8px; border-radius: 10px; margin-left: 8px;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    .result-hero {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 50%, #a7f3d0 100%);
        border-radius: 24px; padding: 48px; text-align: center;
        border: 1px solid #6ee7b7; margin-bottom: 32px;
        box-shadow: 0 4px 24px rgba(16, 185, 129, 0.08);
    }
    .score-card {
        border-radius: 16px; padding: 24px; text-align: center;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04);
        transition: transform 0.2s ease;
    }
    .score-card:hover {
        transform: translateY(-2px);
    }
    .insight-card {
        background: white; border-radius: 12px; padding: 16px 20px;
        border-left: 4px solid #10b981; margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .cta-card {
        background: linear-gradient(135deg, #ecfdf5, #f0fdf4);
        border-radius: 20px; padding: 32px;
        border: 1px solid #86efac; text-align: center;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.08);
    }
    .respondent-card {
        background: white; border-radius: 16px; padding: 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .ai-card {
        background: linear-gradient(135deg, #ecfdf5, #f0fdf4);
        border-radius: 20px; padding: 28px;
        border: 1px solid #6ee7b7; margin-top: 16px;
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.08);
    }
    .progress-bar-container {
        background: white; border-radius: 12px; padding: 16px 24px;
        border: 1px solid #e2e8f0; margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
    .peer-badge {
        background: linear-gradient(135deg, #ecfdf5, #f0fdf4);
        border-radius: 16px; padding: 20px 28px;
        border: 1px solid #86efac; text-align: center;
        box-shadow: 0 2px 12px rgba(16, 185, 129, 0.08);
        margin: 16px 0;
    }
</style>
""", unsafe_allow_html=True)

# -- Session State --
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'responses' not in st.session_state:
    st.session_state.responses = {}

# -- Header --
st.markdown("""
<div class="quiz-header">
    <div style="position: relative; animation: float 3s ease-in-out infinite;">
        <svg width="72" height="72" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg" style="margin-bottom: 12px;">
            <circle cx="32" cy="32" r="28" stroke="rgba(255,255,255,0.3)" stroke-width="2" fill="rgba(255,255,255,0.1)"/>
            <circle cx="32" cy="32" r="8" fill="rgba(255,255,255,0.9)">
                <animate attributeName="r" values="7;9;7" dur="2s" repeatCount="indefinite"/>
            </circle>
            <circle cx="32" cy="14" r="4" fill="rgba(255,255,255,0.8)"/>
            <circle cx="32" cy="50" r="4" fill="rgba(255,255,255,0.8)"/>
            <circle cx="14" cy="32" r="4" fill="rgba(255,255,255,0.8)"/>
            <circle cx="50" cy="32" r="4" fill="rgba(255,255,255,0.8)"/>
            <circle cx="18" cy="18" r="3" fill="rgba(255,255,255,0.6)"/>
            <circle cx="46" cy="18" r="3" fill="rgba(255,255,255,0.6)"/>
            <circle cx="18" cy="46" r="3" fill="rgba(255,255,255,0.6)"/>
            <circle cx="46" cy="46" r="3" fill="rgba(255,255,255,0.6)"/>
            <line x1="32" y1="24" x2="32" y2="18" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
            <line x1="32" y1="40" x2="32" y2="46" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
            <line x1="24" y1="32" x2="18" y2="32" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
            <line x1="40" y1="32" x2="46" y2="32" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
            <line x1="26" y1="26" x2="21" y2="21" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
            <line x1="38" y1="26" x2="43" y2="21" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
            <line x1="26" y1="38" x2="21" y2="43" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
            <line x1="38" y1="38" x2="43" y2="43" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
        </svg>
    </div>
    <p class="quiz-title">AI Readiness Assessment</p>
    <p class="quiz-subtitle">Understand where your organization stands on the AI maturity curve — and what to do next.</p>
    <p style="margin: 20px 0 0 0; font-size: 14px; color: rgba(255,255,255,0.85); font-weight: 600; position: relative;">
        <span style="background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; margin: 0 4px;">⏱️ 3 minutes</span>
        <span style="background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; margin: 0 4px;">📊 Instant results</span>
        <span style="background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; margin: 0 4px;">🤖 AI-powered insights</span>
    </p>
</div>
""", unsafe_allow_html=True)

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
            "D) Public Sector / Healthcare / Other regulated"
        ], index=None, placeholder="Select your industry...")

    st.markdown("---")

    # ============================================================
    # SECTION 2: SCORED QUIZ (10 Questions)
    # ============================================================
    st.markdown('<p class="section-label">📊 AI Maturity Assessment</p>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background: #f8fafc; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; border: 1px solid #e2e8f0;">
        <span style="font-size: 14px; color: #475569;">💡 Answer honestly based on where your organization is <em>today</em>, not where you aspire to be.</span>
    </div>
    """, unsafe_allow_html=True)

    questions = [
        {
            "num": 1, "icon": "🎯",
            "text": "How would you describe your organization's current relationship with AI?",
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
            "text": "How is AI ownership structured within your organization?",
            "options": [
                "A) No clear owner",
                "B) Individual champions, uncoordinated",
                "C) Dedicated team, siloed by department",
                "D) Centralized AI CoE, enterprise-wide"
            ],
            "dimension": "Governance & Talent",
            "dim_color": "#0ea5e9", "dim_bg": "#f0f9ff"
        },
        {
            "num": 3, "icon": "🚀",
            "text": "How many AI use cases does your organization currently have live in production (not pilots)?",
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
            "text": "How would you rate your organization's data readiness?",
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
            "text": "Does your organization have in-house skills to build/deploy/maintain AI without external help?",
            "options": [
                "A) No dedicated talent",
                "B) Small team, stretched thin",
                "C) Dedicated team, skill gaps",
                "D) Fully staffed, specialized"
            ],
            "dimension": "Governance & Talent",
            "dim_color": "#0ea5e9", "dim_bg": "#f0f9ff"
        },
        {
            "num": 7, "icon": "📈",
            "text": "How does your organization measure the success or ROI of AI initiatives?",
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
            <span style="font-size: 13px; font-weight: 600; color: #1e293b;">📝 Progress</span>
            <span style="font-size: 13px; font-weight: 700; color: #059669;">{answered_count}/10 questions answered</span>
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
            <span style="font-size: 13px; color: #64748b;">🔒 Your responses are confidential</span>
            <p style="font-size: 11px; color: #94a3b8; margin: 8px 0 0 0; line-height: 1.5; max-width: 500px; display: inline-block;">
                By submitting this survey, you consent to the use of your information to assess your organisation's AI readiness and to support follow-up activities, engagement, and the provision of relevant Deloitte services. To view our Privacy statement, please visit <a href="https://www.deloitte.com/southeast-asia/en/legal/privacy.html?icid=bottom_privacy" target="_blank" style="color: #059669;">Deloitte Privacy</a>.
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
        level_desc = "Your organization is in early stages of AI adoption. Focus on identifying high-value use cases and building foundational data capabilities."
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
        level_desc = "AI is embedded in your strategy across functions. Focus on optimization, advanced governance, and competitive differentiation."

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
    with st.spinner("🔍 Analyzing your responses with AI..."):

        # Display results hero
        st.markdown(f"""
        <div class="result-hero">
            <p style="font-size: 56px; margin: 0 0 4px 0;">{level_icon}</p>
            <p style="font-size: 14px; color: #059669; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 8px 0;">Your AI Maturity Level</p>
            <p style="font-size: 52px; font-weight: 800; color: {level_color}; margin: 0 0 12px 0;">{level}</p>
            <p style="font-size: 16px; color: #475569; margin: 0; max-width: 600px; display: inline-block; line-height: 1.6;">{level_desc}</p>
        </div>
        """, unsafe_allow_html=True)

        # Score breakdown
        st.markdown("### 📊 Score Breakdown")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
            <div class="score-card" style="background: #ecfdf5; border: 1px solid #a7f3d0;">
                <div style="font-size: 24px; margin-bottom: 8px;">🎯</div>
                <div style="font-size: 11px; color: #059669; font-weight: 700; text-transform: uppercase;">Strategy & Leadership</div>
                <div style="font-size: 32px; font-weight: 800; color: #1e293b; margin-top: 8px;">{strategy_score}<span style="font-size: 16px; color: #94a3b8;">/8</span></div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="score-card" style="background: #f0f9ff; border: 1px solid #bae6fd;">
                <div style="font-size: 24px; margin-bottom: 8px;">🛡️</div>
                <div style="font-size: 11px; color: #0ea5e9; font-weight: 700; text-transform: uppercase;">Governance & Talent</div>
                <div style="font-size: 32px; font-weight: 800; color: #1e293b; margin-top: 8px;">{governance_score}<span style="font-size: 16px; color: #94a3b8;">/12</span></div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="score-card" style="background: #ecfdf5; border: 1px solid #a7f3d0;">
                <div style="font-size: 24px; margin-bottom: 8px;">⚙️</div>
                <div style="font-size: 11px; color: #10b981; font-weight: 700; text-transform: uppercase;">Data & Technology</div>
                <div style="font-size: 32px; font-weight: 800; color: #1e293b; margin-top: 8px;">{data_tech_score}<span style="font-size: 16px; color: #94a3b8;">/8</span></div>
            </div>
            """, unsafe_allow_html=True)

        # Radar chart (pure SVG - no external dependencies)
        st.markdown("### 🕸️ Dimension Radar")

        # Calculate percentage values for each dimension
        strat_pct = strategy_score / 8 * 100
        gov_pct = governance_score / 12 * 100
        data_pct = data_tech_score / 8 * 100

        # SVG radar chart - equilateral triangle with 3 axes
        cx, cy, radius = 150, 150, 120
        angles = [-90, 30, 150]
        axis_pts = [(cx + radius * m.cos(m.radians(a)), cy + radius * m.sin(m.radians(a))) for a in angles]
        data_pts = [(cx + radius * (v/100) * m.cos(m.radians(a)), cy + radius * (v/100) * m.sin(m.radians(a)))
                    for a, v in zip(angles, [strat_pct, gov_pct, data_pct])]

        grid_svg = ""
        for ring_pct in [25, 50, 75, 100]:
            ring_r = radius * ring_pct / 100
            pts = " ".join([f"{cx + ring_r * m.cos(m.radians(a))},{cy + ring_r * m.sin(m.radians(a))}" for a in angles])
            grid_svg += f'<polygon points="{pts}" fill="none" stroke="#e2e8f0" stroke-width="1"/>'

        axes_svg = "".join([f'<line x1="{cx}" y1="{cy}" x2="{p[0]}" y2="{p[1]}" stroke="#e2e8f0" stroke-width="1"/>' for p in axis_pts])
        data_polygon = " ".join([f"{p[0]},{p[1]}" for p in data_pts])

        label_offset = 18
        labels = [
            (cx + (radius + label_offset) * m.cos(m.radians(-90)), cy + (radius + label_offset) * m.sin(m.radians(-90)) - 4, "Strategy & Leadership", f"{strat_pct:.0f}%"),
            (cx + (radius + label_offset) * m.cos(m.radians(30)) + 10, cy + (radius + label_offset) * m.sin(m.radians(30)) + 8, "Governance & Talent", f"{gov_pct:.0f}%"),
            (cx + (radius + label_offset) * m.cos(m.radians(150)) - 10, cy + (radius + label_offset) * m.sin(m.radians(150)) + 8, "Data & Technology", f"{data_pct:.0f}%"),
        ]

        labels_svg = ""
        for lx, ly, name, val in labels:
            anchor = "middle"
            if "Governance" in name:
                anchor = "start"
            elif "Data" in name:
                anchor = "end"
            labels_svg += f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="11" font-weight="bold" fill="#1e293b">{name}</text>'
            labels_svg += f'<text x="{lx}" y="{ly + 14}" text-anchor="{anchor}" font-size="11" font-weight="600" fill="#059669">{val}</text>'

        radar_svg = f"""
        <div style="display: flex; justify-content: center; margin: 16px 0;">
            <svg width="320" height="320" viewBox="0 0 300 300" xmlns="http://www.w3.org/2000/svg">
                {grid_svg}
                {axes_svg}
                <polygon points="{data_polygon}" fill="rgba(16, 185, 129, 0.15)" stroke="#059669" stroke-width="2.5"/>
                <circle cx="{data_pts[0][0]}" cy="{data_pts[0][1]}" r="5" fill="#059669"/>
                <circle cx="{data_pts[1][0]}" cy="{data_pts[1][1]}" r="5" fill="#059669"/>
                <circle cx="{data_pts[2][0]}" cy="{data_pts[2][1]}" r="5" fill="#059669"/>
                {labels_svg}
            </svg>
        </div>
        """
        st.markdown(radar_svg, unsafe_allow_html=True)

        # Maturity bar
        st.markdown("### 📏 Overall Maturity Score")
        st.markdown(f"""
        <div style="margin: 16px 0; background: white; border-radius: 16px; padding: 24px; border: 1px solid #e2e8f0; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                <span style="font-size: 14px; color: #64748b; font-weight: 600;">Progress</span>
                <span style="font-size: 14px; font-weight: 700; color: {level_color};">{total_maturity}/{max_maturity} ({pct:.0f}%)</span>
            </div>
            <div style="background: #e2e8f0; border-radius: 10px; height: 16px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #6ee7b7, #10b981, #059669); width: {pct}%; height: 100%; border-radius: 10px; transition: width 0.5s ease;"></div>
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
                        <p style="font-size: 18px; font-weight: 800; color: #065f46; margin: 8px 0 4px 0;">You scored higher than {percentile}% of {industry_short} respondents</p>
                        <p style="font-size: 13px; color: #047857; margin: 0;">Based on {total_peers} responses in your industry</p>
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
            insights.append(("⚠️", "Scaling Without Governance", "You have production AI but limited governance. This creates risk as you scale — prioritize a formal AI risk framework.", "#f59e0b"))
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
                <div style="font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 4px;">{icon} {title}</div>
                <div style="font-size: 13px; color: #475569; line-height: 1.5;">{desc}</div>
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
            escaped_prompt = prompt.replace("'", "''")
            sql_query = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('mistral-large2', '{escaped_prompt}') AS RESPONSE"
            ai_result = run_sql(sql_query)
            ai_insights = ai_result[0]["RESPONSE"] if ai_result else ""
            if ai_insights:
                st.markdown("### 🤖 AI-Powered Holistic Analysis")
                st.markdown('<span style="font-size: 12px; color: #059669; font-weight: 600;">✨ Powered by Snowflake Cortex</span>', unsafe_allow_html=True)
                st.markdown(f"""
                <div class="ai-card">
                    <div style="font-size: 11px; color: #059669; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;">🧠 Cortex AI Analysis</div>
                    <div style="font-size: 14px; color: #1e293b; line-height: 1.7;">{ai_insights}</div>
                </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass

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
        <p style="font-size: 17px; color: #1e293b; font-weight: 700; margin: 0 0 8px 0;">Recommended Next Step</p>
        <p style="font-size: 15px; color: #475569; margin: 0; line-height: 1.6;">{cta}</p>
    </div>
    """, unsafe_allow_html=True)

    # Respondent summary
    st.markdown("---")
    st.markdown("### 👤 Respondent Details")
    st.markdown(f"""
    <div class="respondent-card">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div><span style="font-size: 12px; color: #059669; font-weight: 600; text-transform: uppercase;">Name</span><br><span style="font-size: 14px; color: #1e293b;">{r.get('name', '')}</span></div>
            <div><span style="font-size: 12px; color: #059669; font-weight: 600; text-transform: uppercase;">Email</span><br><span style="font-size: 14px; color: #1e293b;">{r.get('email', '')}</span></div>
            <div><span style="font-size: 12px; color: #059669; font-weight: 600; text-transform: uppercase;">Company</span><br><span style="font-size: 14px; color: #1e293b;">{r.get('company', '')}</span></div>
            <div><span style="font-size: 12px; color: #059669; font-weight: 600; text-transform: uppercase;">Role</span><br><span style="font-size: 14px; color: #1e293b;">{r.get('role', '')}</span></div>
            <div><span style="font-size: 12px; color: #059669; font-weight: 600; text-transform: uppercase;">Industry</span><br><span style="font-size: 14px; color: #1e293b;">{r.get('industry', '')}</span></div>
            <div><span style="font-size: 12px; color: #059669; font-weight: 600; text-transform: uppercase;">Biggest Blocker</span><br><span style="font-size: 14px; color: #1e293b;">{r.get('q8', '')} {r.get('q8_other', '')}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
