import sqlite3
import os
from datetime import datetime

# Database path - Ye file 'data' folder mein banegi
DB_PATH = os.path.join("data", "documents.db")

def init_db():
    """
    Initializes Database and Table structure
    """
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table structure updated to include all required fields
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            pan_no TEXT,
            dob TEXT,
            aadhaar_no TEXT,
            phone_no TEXT,
            pincode TEXT,
            sgpi TEXT,
            college_name TEXT,
            semester TEXT,
            uploaded_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_final_employee(data):
    """
    Saves verified metadata into the employee_master table
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO employee_master (
            full_name, pan_no, dob, aadhaar_no, phone_no, pincode, 
            sgpi, college_name, semester, uploaded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get('full_name'),
        data.get('pan_no'),
        data.get('dob'),
        data.get('aadhaar_no'),
        data.get('phone_no'),
        data.get('pincode'),
        data.get('sgpi'),
        data.get('college'),
        data.get('semester'),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()
    print("✨ Data successfully saved to employee_master table!")

# Helper function to prevent ImportErrors in other legacy files
def save_document_metadata(**kwargs):
    pass