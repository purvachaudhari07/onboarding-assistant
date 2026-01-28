import pandas as pd
import os
from groq import Groq
from langgraph.graph import StateGraph, END
from app.utils.audio_handler import transcribe_audio_local
import json

# --- Imports from your files ---
from app.orchestrator.state import OnboardingState
from app.utils.db_manager import log_orchestrator, log_agent, get_db_connection, save_final_employee
from app.agents.documents.ocr_engine import analyze_document_v2
from app.agents.documents.storage import save_documents
# --- Imports for Chatbot (Added to top of graph.py) ---
from app.agents.policy.loader import load_policy_documents
from app.agents.policy.vectorstore import create_vector_store
import os
from groq import Groq
from langgraph.graph import StateGraph, END


# Email Logic Import 
from app.agents.policy.welcome_sender import get_unique_email 


# Initialize Groq Client
client = Groq(api_key="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")

# --- NODE 1: DOCUMENT NODE (OCR + Storage) ---
def document_node(state: OnboardingState):
    

    docs = state.get("uploaded_documents", {}) # dict from UI
    user_id = state.get("user_id", "TEMP_ID")
    
    extracted_data = {}
    verification_errors = []

    # Map keys from UI to OCR types
    process_map = {"pan": "PAN", "aadhar": "AADHAAR", "education_cert": "EDUCATION"}

    for key, ocr_type in process_map.items():
        file = docs.get(key)
        if file:
            success, message, data = analyze_document_v2(file, ocr_type)
            if success:
                extracted_data.update(data)
                log_agent("Document_Agent", "Success", f"Verified {ocr_type}", "Data Extracted")
            else:
                verification_errors.append(f"{ocr_type}: {message}")
        else:
            verification_errors.append(f"Missing {ocr_type}")

    if verification_errors:
        return {"current_node": "documents", "error": " | ".join(verification_errors)}

    # Save to Disk & Metadata DB (Using your storage/metadata logic)
    save_documents(docs, user_id)
    save_final_employee(extracted_data)
    
    log_orchestrator("Orchestrator", "Documents Processed. Moving to Voice.")

    return {
        "user_info": extracted_data,
        "current_node": "voice_intro" # Automatically move to next step
    }

# --- NODE 2: VOICE NODE (High Accuracy Extraction) ---
def voice_node(state: OnboardingState):
    import json
    audio_path = state.get("audio_path")
    user_name = state.get("user_info", {}).get("full_name") or "Unknown User"
    
    try:
        clean_text = transcribe_audio_local(audio_path)
        
        # We tell the model to be a "Senior Technical Recruiter" to increase accuracy
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": """You are a Senior Technical Recruiter. 
                 Extract data from the transcript. 
                 Return ONLY a JSON object with these keys:
                 {
                   "confidence": "High Confidence" or "Low Confidence",
                   "tech_skills": ["Python", "Java", "AI", etc.],
                   "soft_skills": ["Communication", "Leadership",etc.],
                   "summary": "Short behavioral summary"
                 }"""},
                {"role": "user", "content": f"Transcript: {clean_text}"}
            ],
            response_format={"type": "json_object"} 
        )
        
        res = json.loads(completion.choices[0].message.content)
        
        # HIGHLIGHTING LOGIC: We format the skills clearly for the Excel sheet
        t_skills = ", ".join(res.get("tech_skills", [])) if res.get("tech_skills") else "None detected"
        s_skills = ", ".join(res.get("soft_skills", [])) if res.get("soft_skills") else "None detected"
        
        # This string goes into your "AI Personality Insight" column
        final_insight = f"TECHNICAL: {t_skills} | SOFT SKILLS: {s_skills} | SUMMARY: {res.get('summary')}"

        return {
            "sentiment_label": res.get("confidence", "Low Confidence"),
            "personality_summary": final_insight,
            "transcript": clean_text,
            "current_node": "policy_chatbot" 
        }
    except Exception as e:
        return {"current_node": "voice_intro", "error": str(e)}
    

# --- NODE 3: POLICY CHATBOT NODE ---
def policy_chatbot_node(state: OnboardingState):
    print("🔄 [NODE]: Entering Policy Chatbot...")
    

    user_query = state.get("last_user_query")
    ai_response = state.get("last_ai_response")
    
    if user_query and ai_response:

        log_agent("Policy_Chatbot", "Conversation", user_query, ai_response)
        log_orchestrator("Orchestrator", "Chatbot conversation logged.")

    return {
        "current_node": "policy_chatbot",
        "onboarding_status": "reading_policy"
    }

# --- NODE 4: QUIZ NODE 
def quiz_node(state: OnboardingState):
    
    try:
        
        score = int(float(state.get("quiz_score", 0)))
        attempts = int(state.get("quiz_attempts", 0))
    except (ValueError, TypeError):
        score = 0
        attempts = 0
    
    # Passing criteria: 60%
    passed = score >= 60
    
    
    print(f"✅ GRAPH DEBUG: Score received: {score}%, Attempts: {attempts}")

    return {
        "quiz_score": score,      
        "quiz_attempts": attempts, 
        "current_node": "final_assessment" if passed else "policy_quiz"
    }
def final_assessment_node(state: OnboardingState):
  

    # 1. Path Setup
    folder_path = "results"
    if not os.path.exists(folder_path): os.makedirs(folder_path)
    file_path = os.path.join(folder_path, "screening_results.xlsx")

    # 2. Data Fetch (Ensure keys match Dashboard)
    user_name = state.get("user_info", {}).get("full_name", "Candidate")
    quiz_score = state.get("quiz_score", 0)
    attempts = state.get("quiz_attempts", 0)
    voice_conf = state.get("sentiment_label", "High Confidence") 
    
    
    ai_summary = state.get("personality_summary", "Analysis Pending")

    # 3. Sentiment & Sheet Name Logic
    if quiz_score >= 80:
        sheet_name, sentiment_word = "POSITIVE", "Positive"
    elif quiz_score >= 60:
        sheet_name, sentiment_word = "NEUTRAL", "Neutral"
    else:
        sheet_name, sentiment_word = "NEGATIVE", "Negative"

    # 4. Prepare EXACT Dashboard Structure (Vertical)
    # Metric and Details columns are required
    dashboard_style_data = {
        "Metric": [
            "Candidate Name", 
            "Final Quiz Score", 
            "Quiz Attempts", 
            "Voice Confidence", 
            "Sentiment Result", 
            "Personality Summary"
        ],
        "Details": [
            user_name,
            f"{quiz_score}%",
            attempts,
            voice_conf,
            sentiment_word,
            ai_summary
        ]
    }
    df_new = pd.DataFrame(dashboard_style_data)

    # 5. Writing to Excel (Handling Sheets)
    try:
        all_sheets = {}
        if os.path.exists(file_path):
            with pd.ExcelFile(file_path) as xls:
                for s in xls.sheet_names:
                    all_sheets[s] = pd.read_excel(xls, sheet_name=s)

        if sheet_name in all_sheets:
            # Separation for new entries
            separator = pd.DataFrame([{"Metric": "------------------------", "Details": "--------------------------"}])
            all_sheets[sheet_name] = pd.concat([all_sheets[sheet_name], separator, df_new], ignore_index=True)
        else:
            all_sheets[sheet_name] = df_new

        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            for s_name, df in all_sheets.items():
                df.to_excel(writer, sheet_name=s_name, index=False)
        
        print(f"✅ Excel Updated for {user_name} in {sheet_name}")
    except Exception as e:
        print(f"❌ Excel Error: {e}")

    return {"hr_assessment": sheet_name, "current_node": "email_sender"}
# --- 6. EMAIL SENDER NODE (Fixed Flow) ---
def email_node(state: OnboardingState):
   
    user_info = state.get("user_info", {})
    full_name = user_info.get("full_name", "User Name")
    
    # Email generation logic
    parts = full_name.split()
    f_name = parts[0] if len(parts) > 0 else "user"
    l_name = parts[-1] if len(parts) > 1 else "name"
    
    # welcome_sender.py logic call
    email, prefix = get_unique_email(f_name, l_name)
    
    log_agent("Identity_Agent", "Generated", "Email_ID", email)
    log_orchestrator("Orchestrator", "Onboarding Complete. Moving to Admin Analysis.")
    
    
    return {
        "final_assigned_email": email, 
        "email_prefix": prefix,
        "current_node": "admin_analyzer" # <--- Ab flow yahan jayega
    }
# --- 7. ADMIN ANALYZER NODE ---
def admin_analyzer_node(state: OnboardingState):
    
    log_orchestrator("System", "Generating Final Dashboard Data...")
    return {
        "current_node": "end" 
    }
# --- GRAPH WIRING ---
workflow = StateGraph(OnboardingState)

workflow.add_node("documents", document_node)
workflow.add_node("voice_intro", voice_node)
workflow.add_node("policy_chatbot", policy_chatbot_node)
workflow.add_node("policy_quiz", quiz_node)
workflow.add_node("final_assessment", final_assessment_node)
workflow.add_node("email_sender", email_node)
workflow.add_node("admin_analyzer", admin_analyzer_node) # <--- Naya Node

# 2. Flow Definition (Connections)
workflow.set_entry_point("documents")
workflow.add_edge("documents", "voice_intro")
workflow.add_edge("voice_intro", "policy_chatbot")
workflow.add_edge("policy_chatbot", "policy_quiz")

# Quiz logic decide
workflow.add_edge("policy_quiz", "final_assessment") 

# Final Assessment---> Email
workflow.add_edge("final_assessment", "email_sender")

# Email ---> Admin Analyzer 
workflow.add_edge("email_sender", "admin_analyzer") # <--- Connection change

# Analyzer---> workflow END 
workflow.add_edge("admin_analyzer", END) # <--- Final End point

onboarding_app = workflow.compile()