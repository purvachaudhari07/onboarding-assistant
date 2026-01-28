import streamlit as st
import sqlite3
import pandas as pd
import os

# --- IMPORT AGENTS ---
from app.agents.documents.metadata import init_db, save_final_employee, DB_PATH
from app.agents.policy.ui import show_company_policy
from app.agents.policy.quiz import show_policy_quiz
import app.agents.policy.welcome_sender as welcome_sender
from app.agents.documents.ocr_engine import analyze_document_v2
from app.utils.audio_handler import save_audio, transcribe_audio_local
from app.orchestrator.graph import onboarding_app

# --- IMPORT FOR OCR ---
try:
    from app.agents.documents.ocr_engine import analyze_document_v2 as analyze_document
except ImportError:
    from app.agents.documents.ocr_engine import analyze_document_v2

# --- ADD THESE TO YOUR EXISTING IMPORTS ---
from streamlit_mic_recorder import mic_recorder


from app.orchestrator.graph import onboarding_app
from app.utils.audio_handler import save_audio
from app.utils.db_manager import log_agent, log_orchestrator



# ==========================================
# 1. INITIALIZATION & CONFIG
# ==========================================
init_db()
st.set_page_config(
    page_title="# Onboarding Assistant", 
    layout="wide", 
    page_icon="🚀",
    initial_sidebar_state="expanded"
)

# Initialize session state for multi-step navigation
if "current_step" not in st.session_state:
    st.session_state.current_step = "documents"

if 'quiz_attempts_count' not in st.session_state:
    st.session_state.quiz_attempts_count = 0
# Chat history ko maintain karne ke liye (Taaki purani baatein gayab na hon)
if "messages" not in st.session_state:
    st.session_state.messages = []
# Initializing Admin Dashboard state
if "show_admin" not in st.session_state:
    st.session_state.show_admin = False

# --- STEP 1: Top of main.py ---


# --- ISKO DAALEIN (Top of main.py) ---
if "onboarding_state" not in st.session_state:
    st.session_state.onboarding_state = {
        "final_assigned_email": None,
        "quiz_score": 0,
        "quiz_attempts": 0,
        "sentiment_label": "N/A",
        "personality_summary": "N/A",
        "final_remark": "Pending"
    }

# ==========================================
# 2. CUSTOM CSS - COMPLETE STYLING
# ==========================================
st.markdown("""
<style>
    /* ===== IMPORTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* ===== GLOBAL STYLES ===== */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background - Beautiful gradient */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important;
        min-height: 100vh;
    }
    
    .block-container { 
        padding: 1.5rem 2rem !important; 
        max-width: 1400px;
    }
    
    /* Content wrapper for better contrast */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    }
    
    /* Smooth Animations */
    [data-testid="stVerticalBlock"] {
        animation: fadeIn 0.4s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    /* ===== SIDEBAR STYLING - Matching theme ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
        color: #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.15) !important;
        margin: 1.5rem 0 !important;
    }
    
    /* ===== PROGRESS STEPS IN SIDEBAR ===== */
    .step-item {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        margin: 6px 0;
        border-radius: 10px;
        transition: all 0.3s ease;
        font-size: 14px;
    }
    
    .step-active {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.25) 100%);
        border-left: 4px solid #667eea;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .step-completed {
        background: rgba(16, 185, 129, 0.2);
        border-left: 4px solid #10B981;
    }
    
    .step-pending {
        background: rgba(255, 255, 255, 0.05);
        border-left: 4px solid #475569;
        opacity: 0.6;
    }
    
    /* ===== PROGRESS BAR ===== */
    .progress-container {
        background: rgba(255,255,255,0.15);
        border-radius: 20px;
        height: 10px;
        overflow: hidden;
        margin: 0.8rem 0;
    }
    
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        border-radius: 20px;
        transition: width 0.6s ease;
        background-size: 200% 100%;
        animation: shimmer 2s infinite linear;
    }
    
    /* ===== MAIN HEADER BANNER ===== */
    .main-header {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 2rem 2.5rem;
        border-radius: 20px;
        margin-bottom: 2.5rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.5);
    }
    
    .main-header h2 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        color: #4a5568;
        font-size: 1rem;
    }
    
    /* ===== DOCUMENT CARDS - SMALLER & BEAUTIFUL ===== */
    .doc-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(255, 255, 255, 0.5);
        border-radius: 16px;
        padding: 1rem 0.8rem;
        text-align: center;
        transition: all 0.3s ease;
        height: 100%;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        min-height: 140px;
        max-width: 280px;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .doc-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 30px rgba(0,0,0,0.2);
        border-color: rgba(102, 126, 234, 0.6);
    }
    
    .doc-card-icon {
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }
    
    .doc-card-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0;
    }
    
    /* ===== STATUS BADGES - WITH PROPER SPACING ===== */
    .status-verified {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        color: #065f46;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        border: 1px solid #6ee7b7;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        justify-content: center;
    }
    
    .status-pending {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        color: #92400e;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        border: 1px solid #fcd34d;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        justify-content: center;
    }
    
    .status-locked {
        background: rgba(241, 245, 249, 0.9);
        color: #64748b;
        padding: 8px 16px;
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.85rem;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        border: 1px solid #cbd5e1;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        justify-content: center;
    }
    
    /* ===== SUCCESS CARD ===== */
    .success-card {
        background: rgba(236, 253, 245, 0.95);
        backdrop-filter: blur(10px);
        border: 2px solid #6ee7b7;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 2rem 0 1.5rem 0;
        box-shadow: 0 8px 25px rgba(16, 185, 129, 0.2);
    }
    
    .success-card h4 {
        margin: 0;
        color: #000000; #############
        font-size: 1.2rem;
    }
    
    .success-card p {
        margin: 0.5rem 0 0 0;
        color: #000000; ##############
    }
/* ==========================================
   ULTIMATE BLUE & GREEN REMOVER (FINAL)
   ========================================== */

/* 1. Target Blue Box (st.info) aur uske andar ka text */
div[data-testid="stNotification"][data-status="info"],
div[data-testid="stNotification"] {
    background-color: rgba(255, 255, 255, 0.15) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
}

/* 2. Target Green Box (st.success) jo email page par hai */
div[data-testid="stNotification"][data-status="success"] {
    background-color: rgba(255, 255, 255, 0.15) !important;
    border: 1px solid rgba(0, 255, 204, 0.4) !important;
}

/* 3. Force WHITE text inside ALL notifications (Blue/Green bars) */
div[data-testid="stNotification"] p, 
div[data-testid="stNotification"] div,
div[data-testid="stNotification"] span,
div[data-testid="stNotification"] b {
    color: #FFFFFF !important;
    text-shadow: none !important;
}

/* 4. Chatbot Response Box (Jaisa pehle tha, but refined) */
.chatbot-response-box {
    background: rgba(255, 255, 255, 0.12) !important;
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.25) !important;
    border-radius: 12px !important;
    padding: 20px !important;
    margin: 20px 0 !important;
}

/* 5. Force white for every single child inside chatbot box */
.chatbot-response-box * {
    color: #FFFFFF !important;
}

/* 6. Email ID (code snippet) color fix */
code {
    color: #FFFFFF !important; 
    background: rgba(0, 0, 0, 0.3) !important;
}
    /* ===== INFO CARD ===== */
    .info-card {
        background: rgba(239, 246, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 2px solid #93c5fd;
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 1rem 0 1.5rem 0;
    }
    
    .info-card h4 {
        margin: 0;
        color: #1e40af;
    }
    
    .info-card p {
        margin: 0.5rem 0 0 0;
        color: #1d4ed8;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Secondary Button Style */
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        box-shadow: none !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.15) !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
    }
    
    /* ===== FILE UPLOADER - BEAUTIFUL DESIGN ===== */
    [data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 2px dashed rgba(102, 126, 234, 0.4);
        border-radius: 12px;
        padding: 1rem;
        transition: all 0.3s ease;
        margin-top: 1rem;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #667eea;
        background: rgba(245, 243, 255, 0.95);
    }
    
    [data-testid="stFileUploader"] section {
        padding: 0.5rem;
    }
    
    /* ===== EXPANDER - PROPER SPACING ===== */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.9) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(229, 231, 235, 0.8) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        padding: 0.7rem 1rem !important;
        margin-top: 0.8rem !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(248, 250, 252, 0.95) !important;
        border-color: rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Expander content spacing */
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.85) !important;
        backdrop-filter: blur(10px) !important;
        padding: 1rem !important;
        border-radius: 0 0 8px 8px !important;
        margin-top: -5px !important;
    }
    
    /* ===== POLICY PAGE ===== */
    .policy-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(229, 231, 235, 0.8);
        border-radius: 16px;
        padding: 2rem;
        max-height: 500px;
        overflow-y: auto;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    /* ===== QUIZ PAGE ===== */
    .quiz-question {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 2px solid rgba(229, 231, 235, 0.8);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    .quiz-question h4 {
        color: #1e293b;
        margin-bottom: 1rem;
    }
    
    /* ===== EMAIL PAGE ===== */
    .email-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border: 2px solid #86efac;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(16, 185, 129, 0.25);
    }
    
    .credential-box {
        background: #1e293b;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        font-family: 'Monaco', 'Consolas', monospace;
        color: #10b981;
        font-size: 1.1rem;
    }
    
    /* ===== CELEBRATION ===== */
    .celebration {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 3rem 2rem;
        text-align: center;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
        border: 2px solid rgba(255, 255, 255, 0.5);
    }
    
    .celebration h1 {
        font-size: 3rem;
        margin: 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .celebration p {
        font-size: 1.2rem;
        color: #4a5568;
        margin: 1rem 0 0 0;
    }
    
    /* ===== COLUMNS SPACING ===== */
    [data-testid="column"] {
        padding: 0 0.6rem !important;
    }
    
    /* First and last column reduce outer padding */
    [data-testid="column"]:first-child {
        padding-left: 0 !important;
    }
    
    [data-testid="column"]:last-child {
        padding-right: 0 !important;
    }
    /* ===== STREAMLIT TOP BAR - MATCH BACKGROUND ===== */
    header[data-testid="stHeader"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%) !important;
}
    
    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ===== RESPONSIVE FIXES ===== */
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem !important;
        }
        .main-header {
            padding: 1.5rem;
        }
        .main-header h2 {
            font-size: 1.4rem;
        }
        .doc-card {
            min-height: 130px;
            padding: 0.8rem;
            max-width: 100%;
        }
        .doc-card-icon {
            font-size: 2rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_progress_info():
    """Calculate progress based on current step"""
    steps = ["documents", "voice_intro", "policy_read", "policy_quiz", "email"]
    current = st.session_state.current_step
    current_index = steps.index(current) if current in steps else 0
    return current_index + 1, len(steps), ((current_index + 1) / len(steps)) * 100

def render_sidebar_progress():
    """Render the progress bar in sidebar"""
    step_num, total, percent = get_progress_info()
    st.markdown(f"""
        <div style="margin: 1rem 0;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                <span style="font-size: 13px; color: #94a3b8;">Progress</span>
                <span style="font-size: 13px; color: #94a3b8; font-weight: 600;">{int(percent)}%</span>
            </div>
            <div class="progress-container">
                <div class="progress-fill" style="width: {percent}%;"></div>
            </div>
            <p style="text-align: center; color: #64748b; font-size: 13px; margin-top: 8px;">
                Step {step_num} of {total}
            </p>
        </div>
    """, unsafe_allow_html=True)

def render_step_item(icon, label, is_completed, is_active):
    """Render a single step item in sidebar"""
    if is_completed:
        status_class = "step-completed"
        status_icon = "✅"
    elif is_active:
        status_class = "step-active"
        status_icon = "▶️"
    else:
        status_class = "step-pending"
        status_icon = "○"
    
    st.markdown(f"""
        <div class="step-item {status_class}">
            <span style="margin-right: 12px; font-size: 16px;">{status_icon}</span>
            <span style="font-size: 14px;">{icon} {label}</span>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 4. SIDEBAR
# ==========================================
with st.sidebar:
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        if os.path.exists("download.jpg"):
            st.image("download.jpg")

    st.markdown("""
        <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
            <h2 style="margin: 0; font-size: 1.3rem; font-weight: 700; color: #f1f5f9 !important;">
                Onboarding Portal
            </h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    render_sidebar_progress()
    st.divider()
    
    # Navigation logic for sidebar indicators
    docs_done = st.session_state.get('edu_v') == True
    voice_done = st.session_state.get('voice_processed') == True
    policy_done = st.session_state.current_step in ["policy_quiz", "email"]
    quiz_done = st.session_state.get("quiz_passed") == True
    email_done = st.session_state.current_step == "email"
    
    render_step_item("📁", "Documents", docs_done, st.session_state.current_step == "documents")
    render_step_item("🎤", "Voice Intro", voice_done, st.session_state.current_step == "voice_intro")
    render_step_item("📋", "Company Policy", policy_done, st.session_state.current_step == "policy_read")
    render_step_item("📝", "Assessment", quiz_done, st.session_state.current_step == "policy_quiz")
    render_step_item("📧", "Credentials", email_done, st.session_state.current_step == "email")
    
    st.divider()
    if st.button("🔄 Start Over", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    # --- ADMIN ACCESS SECTION (Add this at the end of sidebar) ---
    st.divider()
    # Expander use kar rahe hain taaki ye hidden rahe
    with st.sidebar.expander("🛠️ Admin Settings"):
        admin_mode = st.checkbox("Enable Admin Mode")
        if admin_mode:
            # Session state mein mode save kar rahe hain
            st.session_state.app_mode = "Admin Dashboard"
        else:
            st.session_state.app_mode = "Candidate Portal"
# ==========================================
# 5. MAIN CONTENT LOGIC
# ==========================================


import streamlit as st
import pandas as pd
import os

import streamlit as st
import pandas as pd
import os

# Check if Admin Mode is ON
if st.session_state.get("app_mode") == "Admin Dashboard":
    st.title("🛡️ Executive HR Dashboard")
    
    # --- 1. PREMIUM CSS STYLING ---
    st.markdown("""
        <style>
        /* Tab Bar Styling */
        .stTabs [data-baseweb="tab-list"] { gap: 15px; }
        .stTabs [data-baseweb="tab"] {
            height: 55px; background-color: #f0f2f6; border-radius: 12px 12px 0px 0px;
            padding: 10px 30px; font-weight: bold; font-size: 16px;
        }
        /* Color Active Tabs */
        .stTabs [aria-selected="true"]:nth-of-type(1) { background-color: #d4edda !important; color: #155724 !important; border-bottom: 4px solid #28a745 !important; }
        .stTabs [aria-selected="true"]:nth-of-type(2) { background-color: #f8d7da !important; color: #721c24 !important; border-bottom: 4px solid #dc3545 !important; }
        .stTabs [aria-selected="true"]:nth-of-type(3) { background-color: #e2e3e5 !important; color: #383d41 !important; border-bottom: 4px solid #6c757d !important; }

        /* Fancy Expander Header */
        .streamlit-expanderHeader {
            background: linear-gradient(to right, #ffffff, #f8f9fa);
            border-radius: 12px;
            border: 1px solid #e1e4e8;
            margin-bottom: 12px;
            color: #1f2937 !important;
            font-weight: 600 !important;
            padding: 15px !important;
        }

        /* Information Box Styling */
        .info-box {
            padding: 15px; border-radius: 10px; background-color: #f9fafb;
            border-left: 5px solid #6366f1; margin-bottom: 10px;
        }
        </style>
    """, unsafe_allow_html=True)




import streamlit as st
import pandas as pd
import os

# Check if Admin Mode is ON
if st.session_state.get("app_mode") == "Admin Dashboard":
    # --- 1. PREMIUM CSS STYLING ---
    st.markdown("""
        <style>
        /* Fixes top padding and hides duplicate headers */
        .block-container { padding-top: 1rem; }
        
        /* Premium Tab Styling */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            height: 45px; background-color: #f1f3f9; border-radius: 8px 8px 0px 0px;
            padding: 5px 20px; font-weight: bold;
        }
        /* Tab Colors */
        .stTabs [aria-selected="true"]:nth-of-type(1) { background-color: #2ecc7 green !important; color: white !important; }
        .stTabs [aria-selected="true"]:nth-of-type(2) { background-color: #e74c3c !important; color: white !important; }
        .stTabs [aria-selected="true"]:nth-of-type(3) { background-color: #95a5a6 !important; color: white !important; }

        /* Expander Styling */
        .streamlit-expanderHeader {
            background-color: white !important;
            border-radius: 10px !important;
            border: 1px solid #dfe6e9 !important;
            font-weight: bold !important;
            font-size: 16px !important;
        }
        
        /* Clean Insight Text */
        .insight-box {
            color: #2d3436;
            padding: 10px 15px;
            border-left: 5px solid #6c5ce7;
            background-color: #f8f9fa;
            border-radius: 5px;
            font-size: 14px;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. SINGLE TITLE ---
    # This replaces the double title issue
    st.header("🛡️ Executive HR Dashboard")

    passwd = st.text_input("Enter Admin Password:", type="password")
    
    if passwd == "admin123":
        st.success("✅ Access Granted")
        
        # --- 3. SEARCH & DATABASE ---
        search_query = st.text_input("🔍 Search Candidate", placeholder="Enter name...")
        st.divider()
        
        file_path = "results/screening_results.xlsx"
        
        if os.path.exists(file_path):
            xls = pd.ExcelFile(file_path)
            tabs = st.tabs(["🟢 POSITIVE", "🔴 NEGATIVE", "⚪ NEUTRAL"])
            categories = ["POSITIVE", "NEGATIVE", "NEUTRAL"]

            for i, sheet_name in enumerate(categories):
                with tabs[i]:
                    if sheet_name in xls.sheet_names:
                        df = pd.read_excel(file_path, sheet_name=sheet_name)
                        
                        # Logic to separate candidates
                        indices = df[df['Metric'] == 'Candidate Name'].index.tolist()
                        
                        found_any = False
                        for idx, start in enumerate(indices):
                            end = indices[idx+1] if idx+1 < len(indices) else len(df)
                            candidate_block = df.iloc[start:end]
                            
                            # Convert to dict for easy lookup
                            p_data = candidate_block.set_index('Metric')['Details'].to_dict()
                            name = str(p_data.get("Candidate Name", "Unknown"))

                            if search_query.lower() in name.lower():
                                found_any = True
                                
                                # --- 4. CLEAN CANDIDATE CARD ---
                                with st.expander(f"👤 {name.upper()}"):
                                    # Info Grid
                                    col1, col2, col3 = st.columns(3)
                                    col1.metric("📊 Score", p_data.get("Final Quiz Score", "0%"))
                                    col2.metric("🔄 Attempts", p_data.get("Quiz Attempts", "0"))
                                    col3.metric("🎙️ Confidence", p_data.get("Voice Confidence", "N/A"))

                                    st.markdown("---")
                                    
                                    # BEHAVIORAL INSIGHT - Robust Lookup
                                    st.markdown("**🎯 Behavioral Insight**")
                                    # Try every possible name that might be in your Excel
                                    summary = p_data.get("AI Personality Summary", 
                                              p_data.get("Personality Summary", 
                                              "Summary data not found in this record."))
                                    
                                    st.markdown(f'<div class="insight-box">{summary}</div>', unsafe_allow_html=True)
                                    
                                    # INDIVIDUAL DOWNLOAD (Fixed placement & Unique Key)
                                    st.download_button(
                                        label=f"📥 Download {name}'s Report",
                                        data=candidate_block.to_csv(index=False),
                                        file_name=f"{name}_report.csv",
                                        key=f"dl_{i}_{idx}"
                                    )
                        
                        if not found_any:
                            st.info(f"No candidates in {sheet_name}")
                    else:
                        st.info(f"No data for {sheet_name}")
            
            # Master Download
            st.divider()
            with open(file_path, "rb") as f:
                st.download_button("📂 Download Master Excel Report", f, file_name="Full_Report.xlsx", key="master")
                
        else:
            st.warning("No records found.")
            
    elif passwd != "":
        st.error("Incorrect Password")
    
    st.stop()
# ==========================================
# 5. MAIN CONTENT AREA
# ==========================================

# --- PAGE 1: DOCUMENTS ---
if st.session_state.current_step == "documents":
    st.markdown('<div class="main-header"><h2>📁 Document Verification</h2><p>Securely process your identity documents.</p></div>', unsafe_allow_html=True)
    
    # Initialize verification states if not present
    for key in ["pan_v", "aadhar_v", "edu_v"]:
        if key not in st.session_state: 
            st.session_state[key] = False

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown('<div class="doc-card">🪪 PAN Card</div>', unsafe_allow_html=True)
        if st.session_state.pan_v: 
            st.success("Verified ✅")
        else:
            pan = st.file_uploader("PAN", type=["jpg", "png", "jpeg"], key="p_up", label_visibility="collapsed")
            if pan:
                success, msg, data = analyze_document_v2(pan, "PAN")
                if success: 
                    st.session_state.pan_data = data
                    st.session_state.pan_v = True
                    st.rerun()
                else:
                    st.error("Invalid PAN")

    with c2:
        st.markdown('<div class="doc-card">🆔 Aadhaar Card</div>', unsafe_allow_html=True)
        if not st.session_state.pan_v: 
            st.info("🔒 Pending PAN")
        elif st.session_state.aadhar_v: 
            st.success("Verified ✅")
        else:
            aa = st.file_uploader("Aadhaar", type=["jpg", "png", "jpeg"], key="a_up", label_visibility="collapsed")
            if aa:
                success, msg, data = analyze_document_v2(aa, "AADHAAR")
                if success:
                    st.session_state.aadhaar_data = data
                    st.session_state.aadhar_v = True
                    st.rerun()
                else:
                    st.error("Invalid Aadhaar")

    with c3:
        st.markdown('<div class="doc-card">🎓 Education</div>', unsafe_allow_html=True)
        if not st.session_state.aadhar_v: 
            st.info("🔒 Pending Aadhaar")
        elif st.session_state.edu_v: 
            st.success("Verified ✅")
        else:
            edu = st.file_uploader("Edu", type=["jpg", "png", "jpeg"], key="e_up", label_visibility="collapsed")
            if edu:
                success, msg, data = analyze_document_v2(edu, "EDUCATION")
                if success:
                    st.session_state.edu_data = data
                    st.session_state.edu_v = True
                    st.balloons()
                    st.rerun()

    # --- FINAL SUBMISSION LOGIC ---
    if st.session_state.pan_v and st.session_state.aadhar_v and st.session_state.edu_v:
        if "doc_processed" not in st.session_state:
            with st.spinner("Finalizing Document Verification..."):
                # Data Fetching safely
                pan_info = st.session_state.get('pan_data', {})
                aa_info = st.session_state.get('aadhaar_data', {})
                
                payload = {
                    'full_name': pan_info.get('full_name', 'Employee'),
                    'pan_no': pan_info.get('pan_no', 'N/A'),
                    'aadhaar_no': aa_info.get('aadhaar_no', 'N/A'),
                }
                
                # Database & Orchestrator Update
                save_final_employee(payload)
                
                # Sync this with the global onboarding state
                st.session_state.onboarding_state['user_info'] = payload
                
                # Trigger Agent
                onboarding_app.invoke({"user_info": payload, "current_node": "documents"})
                
                # Move to next step
                st.session_state.doc_processed = True
                st.session_state.current_step = "voice_intro"
                st.rerun()

# ==========================================
# PAGE 2: VOICE INTRODUCTION (Auto-Submit Version)
# ==========================================
elif st.session_state.current_step == "voice_intro":
    raw_name = st.session_state.get('pan_data', {}).get('full_name', 'New Employee')
    user_name = raw_name.title()

    st.markdown(f"""
        <div class="main-header">
            <h2>🎤 Voice Introduction</h2>
            <p>Welcome, <span style="color: #764ba2;"><b>{user_name}</b></span>!</p>
        </div>
    """, unsafe_allow_html=True)

    # 1. Talking Bot Script (Indian Accent)
    if "instruction_played" not in st.session_state:
        st.components.v1.html(f"""
            <script>
                var msg = new SpeechSynthesisUtterance();
                msg.text = "Hello {user_name}, I am your onboarding assistant. Please record your introduction now.";
                var voices = window.speechSynthesis.getVoices();
                var indianVoice = voices.find(v => v.lang === 'en-IN');
                if(indianVoice) msg.voice = indianVoice;
                msg.rate = 0.85;
                window.speechSynthesis.speak(msg);
            </script>
        """, height=0)
        st.session_state.instruction_played = True

    # 2. Recorder (Auto-Trigger Logic)
    audio = mic_recorder(
        start_prompt=f"Start Recording 🎤", 
        stop_prompt="Stop & Process ✅", 
        key='intro_mic'
    )

    # 3. AUTO-PROCESS
    if audio and "voice_processed" not in st.session_state:
        with st.spinner("Processing your introduction..."):
            # Save audio
            path = save_audio(audio['bytes'])
            
            # Direct Graph Invoke (No button needed)
            initial_state = {
                "user_info": st.session_state.get('pan_data', {}),
                "audio_path": path,
                "current_node": "voice_node"
            }
            
            result = onboarding_app.invoke(initial_state)
            
            # Update State & Move Forward
            st.session_state.onboarding_state.update(result)
            st.session_state.voice_processed = True
            st.session_state.current_step = "policy_read" 
            st.rerun()

    
    if "voice_processed" in st.session_state:
        st.success("Redirecting to Policy Page...")
# --- PAGE 3: POLICY ---
elif st.session_state.current_step == "policy_read":
    show_company_policy() 
    if st.button("I've Read - Start Quiz 📝", use_container_width=True, type="primary"):
        st.session_state.current_step = "policy_quiz"
        st.rerun()

# --- PAGE 4: QUIZ (Updated in main.py) ---
elif st.session_state.current_step == "policy_quiz":
    st.markdown('<div class="main-header"><h2>📝 Knowledge Assessment</h2></div>', unsafe_allow_html=True)
    show_policy_quiz() 
    
    # Jab quiz pass ho jaye aur final step abhi tak trigger na hua ho
    if st.session_state.get("quiz_passed") and 'final_step_triggered' not in st.session_state:
        with st.spinner("Finalizing Onboarding..."):
            
            # quiz.py se real data uthana
            actual_score = st.session_state.get("quiz_score", 0) 
            actual_attempts = st.session_state.get("quiz_attempts_count", 1)

            # Invoke with dynamic data
            res = onboarding_app.invoke({
                **st.session_state.onboarding_state, 
                "quiz_score": actual_score,         # 100 ki jagah actual variable
                "quiz_attempts": actual_attempts,   # Actual attempts
                "current_node": "policy_quiz"
            })
            
            st.session_state.onboarding_state.update(res)
            st.session_state.final_step_triggered = True
            st.session_state.current_step = "email"
            st.rerun()

# --- PAGE 5: EMAIL & SUCCESS ---
elif st.session_state.current_step == "email":
    st.markdown('<div style="text-align:center;"><h2 style="color:white;">🎊 Welcome Aboard!</h2></div>', unsafe_allow_html=True)
    
    
    welcome_sender.show_email_screen()

    st.success("Your official identity has been created successfully.")
    
    # st.info("💡 You can now safely close this window. HR will contact you if your profile matches the requirements.")

    st.divider()
    
    # 3. Final Finish button jo sab clear karke restart karega
    if st.button("✅ Complete Onboarding", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()
# ==========================================
# FOOTER (Always Visible)
# ==========================================
st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0; margin-top: 3rem; border-top: 1px solid #e2e8f0;">
        <p style="color: #94a3b8; font-size: 13px;">
            🚀 Intelligent Onboarding Portal v1.0 | Powered by LangGraph & Gemini
        </p>
    </div>
""", unsafe_allow_html=True)