import os
# Fix: Path changed to app.agents and function name synced with metadata.py
from app.agents.documents.metadata import save_final_employee 

BASE_UPLOAD_DIR = os.path.join("data", "uploads")

def save_documents(documents: dict, employee_id: str, employee_data: dict):
    """
    Saves physical files to disk and triggers database storage.
    """
    print("✅ save_documents() CALLED")

    # Create folder for specific employee
    employee_folder = os.path.join(BASE_UPLOAD_DIR, employee_id)
    os.makedirs(employee_folder, exist_ok=True)

    # 1️⃣ Save each file to the local directory
    for document_type, uploaded_file in documents.items():
        if uploaded_file is None:
            continue

        file_path = os.path.join(employee_folder, uploaded_file.name)
        print(f"📂 Saving {document_type} to {file_path}")

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    # 2️⃣ Save the extracted OCR data to the Database
    # This calls the function in metadata.py
    save_final_employee(employee_data)

    print("✅ Files saved + metadata stored in DB")