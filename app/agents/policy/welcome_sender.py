import streamlit as st
import sqlite3
import os

DB_PATH = os.path.join("data", "documents.db")

def get_unique_email(first_name, last_name):
    """Generates a unique email like first.last@sankeysolutions.com"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ensure the table exists in our main database
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generated_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_prefix TEXT UNIQUE,
            full_email TEXT
        )
    """)
    
    base_prefix = f"{first_name.lower()}.{last_name.lower()}"
    
    # Check how many people have this same name combination
    cursor.execute("SELECT COUNT(*) FROM generated_emails WHERE email_prefix LIKE ?", (f"{base_prefix}%",))
    count = cursor.fetchone()[0]
    
    if count == 0:
        final_email = f"{base_prefix}@sankeysolutions.com"
    else:
        # If duplicate exists: first.last1@sankeysolutions.com
        final_email = f"{base_prefix}{count}@sankeysolutions.com"
        
    conn.close()
    return final_email, base_prefix

def save_email_to_db(email_prefix, full_email):
    """Saves the final assigned email to prevent duplicates in future"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO generated_emails (email_prefix, full_email) VALUES (?, ?)", 
                       (email_prefix, full_email))
        conn.commit()
    except:
        pass # Handle if already exists
    conn.close()

def show_email_screen():
    pan_data = st.session_state.get("pan_data", {})
    full_name = pan_data.get("full_name", "Employee Name")
    
    # Name logic...
    parts = full_name.split()
    f_name = parts[0] if len(parts) > 0 else "user"
    l_name = parts[-1] if len(parts) > 1 else "name"

    if "final_assigned_email" not in st.session_state or st.session_state.final_assigned_email is None:
        email, prefix = get_unique_email(f_name, l_name)
        st.session_state.final_assigned_email = email
    
    st.markdown('<h2 style="color: white;">Your Official Identity</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/190/190411.png", width=80) 
    
    with col2:
        # Blue box ki jagah white glass box
        st.markdown(f"""
            <div style="background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255,255,255,0.3); padding: 15px; border-radius: 12px;">
                <p style="color: white !important; margin:0;">📧 <b>Email ID:</b> 
                <span style="color: #00D4FF; font-family: monospace;">{st.session_state.final_assigned_email}</span></p>
            </div>
        """, unsafe_allow_html=True)

    # Green success bar ki jagah white message
    st.markdown("""
        <div style="color: #00FFCC; font-weight: bold; margin-top: 20px; text-align: center;">
            ✅ Your official identity has been created successfully.
        </div>
    """, unsafe_allow_html=True)