import sqlite3
import json

# Define the paths for your two database files
DOC_DB = "documents.db"
REC_DB = "recordings.db"

def get_db_connection():
    """
    Creates and returns a connection to the recordings database.
    This is required by the graph nodes to save voice analysis results.
    """
    conn = sqlite3.connect(REC_DB)
    # This allows us to access columns by name (e.g., row['transcript'])
    conn.row_factory = sqlite3.Row 
    return conn

def init_dbs():
    """
    Initializes both databases and creates all necessary tables if they don't exist.
    Run this once at the start of the application.
    """
    # --- 1. SETUP DOCUMENTS.DB (For OCR & Employee Data) ---
    conn_doc = sqlite3.connect(DOC_DB)
    c_doc = conn_doc.cursor()
    
    # Stores verified employee details from ID cards
    c_doc.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT, pan_no TEXT, dob TEXT,
            aadhaar_no TEXT, phone_no TEXT, pincode TEXT,
            sgpi TEXT, college TEXT, semester TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Logs technical actions taken by OCR agents
    c_doc.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT, status TEXT, task TEXT, result TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn_doc.commit()
    conn_doc.close()

    # --- 2. SETUP RECORDINGS.DB (For AI Flow & Voice Results) ---
    conn_rec = sqlite3.connect(REC_DB)
    c_rec = conn_rec.cursor()
    
    # Tracks the high-level flow of the LangGraph system
    c_rec.execute("""
        CREATE TABLE IF NOT EXISTS orchestrator_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_name TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Stores the actual Voice-to-Text and Sentiment results
    c_rec.execute("""
        CREATE TABLE IF NOT EXISTS voice_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            transcript TEXT,
            sentiment TEXT,
            audio_path TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn_rec.commit()
    conn_rec.close()

def log_agent(agent_name, status, task, result):
    """Logs specific agent actions (like OCR or Sentiment) to the Documents DB."""
    conn = sqlite3.connect(DOC_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO agent_logs (agent_name, status, task, result)
        VALUES (?, ?, ?, ?)
    """, (agent_name, status, task, str(result)))
    conn.commit()
    conn.close()

def log_orchestrator(node_name, message):
    """Logs major system events or decisions to the Recordings DB."""
    conn = sqlite3.connect(REC_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orchestrator_logs (node_name, message)
        VALUES (?, ?)
    """, (node_name, message))
    conn.commit()
    conn.close()

def save_final_employee(data):
    """Saves the final verified employee information after OCR steps."""
    conn = sqlite3.connect(DOC_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO employees (full_name, pan_no, dob, aadhaar_no, phone_no, pincode, sgpi, college, semester)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('full_name'), data.get('pan_no'), data.get('dob'),
        data.get('aadhaar_no'), data.get('phone_no'), data.get('pincode'),
        data.get('sgpi'), data.get('college'), data.get('semester')
    ))
    conn.commit()
    conn.close()

# Ensure tables are created as soon as this script is imported
init_dbs()