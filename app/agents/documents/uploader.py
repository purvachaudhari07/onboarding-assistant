import streamlit as st

def document_upload_ui():
    st.subheader("📄 Upload Required Documents")

    # 1. We rename 'id_proof' to 'pan' so the OCR engine can find it
    pan = st.file_uploader(
        "Upload PAN Card (JPG / JPEG / PNG)",
        type=["jpg", "jpeg", "png"],
        key="pan_uploader"
    )

    # 2. We rename 'address_proof' to 'aadhar' for better clarity
    aadhar = st.file_uploader(
        "Upload Aadhar Card (JPG / JPEG / PNG)",
        type=["jpg", "jpeg", "png"],
        key="aadhar_uploader"
    )

    education_cert = st.file_uploader(
        "Upload Educational Certificate (PDF / JPG)",
        type=["pdf", "jpg", "jpeg"],
        key="education_cert_uploader"
    )

    # The keys here MUST match what main.py is looking for
    return {
        "pan": pan,
        "aadhar": aadhar,
        "education_cert": education_cert
    }
