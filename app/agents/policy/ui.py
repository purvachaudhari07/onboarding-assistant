import streamlit as st
import os
from app.agents.policy.chatbot import policy_chatbot_ui

POLICY_PDF_PATH = os.path.join("data", "policies", "company_policy.pdf")

def show_company_policy():
    st.header("📄 Company Policy")

    with open(POLICY_PDF_PATH, "rb") as f:
        st.download_button(
            "📥 Open Company Policy",
            f,
            file_name="company_policy.pdf",
            mime="application/pdf"
        )

    
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.1); border-left: 5px solid #FFFFFF; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="color: white !important; margin: 0; font-weight: 500;">
                ℹ️ Please read the policy and ask questions below.
            </p>
        </div>
    """, unsafe_allow_html=True)

    policy_chatbot_ui()