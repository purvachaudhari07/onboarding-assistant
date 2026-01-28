import streamlit as st
import random
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.agents.policy.loader import load_policy_documents

def generate_dynamic_questions():
    """AI generates unique and easy MCQs."""
    try:
        docs = load_policy_documents()
        random_page = random.randint(0, max(0, len(docs)-1))
        context = docs[random_page].page_content 

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=st.secrets["GROQ_API_KEY"],
            temperature=0.7, 
            max_tokens=1000
        )

        prompt = ChatPromptTemplate.from_template(
            """
            You are an HR Assistant. Generate 5 EASY Multiple Choice Questions (MCQs) 
            from the policy context provided. 
            Return ONLY a Python-readable list of dictionaries:
            [{{"q": "...", "options": ["A", "B", "C", "D"], "answer": "..."}}]
            Context: {context}
            """
        )

        chain = prompt | llm
        response = chain.invoke({"context": context})
        raw_content = response.content.strip()
        
        # Cleaning logic
        if "```python" in raw_content:
            raw_content = raw_content.split("```python")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
            
        return eval(raw_content)
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []

def show_policy_quiz():
    # 1. Initialization
    if "quiz_questions" not in st.session_state:
        with st.spinner("🤖 Generating questions..."):
            st.session_state.quiz_questions = generate_dynamic_questions()
            st.session_state.quiz_submitted = False
            st.session_state.quiz_score = 0
            st.session_state.quiz_passed = False
            if 'quiz_attempts_count' not in st.session_state:
                st.session_state.quiz_attempts_count = 0

    # 2. Show Quiz Form
    if not st.session_state.get("quiz_submitted"):
        with st.form("dynamic_quiz_form"):
            user_answers = []
            for i, q in enumerate(st.session_state.quiz_questions):
                st.write(f"**Q{i+1}. {q['q']}**")
                ans = st.radio("Choose:", q["options"], index=None, key=f"q_dyn_{i}")
                user_answers.append(ans)
            
            if st.form_submit_button("Submit Assessment"):
                if None in user_answers:
                    st.warning("Please answer all questions.")
                else:
                    # Calculate Score
                    correct_count = sum(1 for i, a in enumerate(user_answers) if a == st.session_state.quiz_questions[i]["answer"])
                    final_percentage = int((correct_count / 5) * 100) # Force Integer for Excel compatibility
                    
                    # Update Total Attempts
                    st.session_state.quiz_attempts_count += 1
                    
                    # --- CRITICAL SYNC WITH ONBOARDING STATE ---
                    if "onboarding_state" in st.session_state:
                        # Hum direct dictionary update kar rahe hain taaki Graph node ise read kar sake
                        st.session_state.onboarding_state["quiz_score"] = final_percentage
                        st.session_state.onboarding_state["quiz_attempts"] = st.session_state.quiz_attempts_count
                    
                    # Update local session state
                    st.session_state.quiz_score = final_percentage
                    st.session_state.quiz_submitted = True
                    st.rerun()

    # 3. Show Results
    else:
        st.write(f"### Your Score: {st.session_state.quiz_score}%")
        
        if st.session_state.quiz_score >= 60: 
            st.success(f"✅ Passed! Attempt #{st.session_state.quiz_attempts_count} was successful.")
            st.session_state.quiz_passed = True
            
            # --- Move to Final Assessment Node ---
            if st.button("Proceed to Final Result"):
                if "onboarding_state" in st.session_state:
                    # Syncing one last time for safety
                    st.session_state.onboarding_state["current_node"] = "final_assessment"
                    st.session_state.onboarding_state["quiz_score"] = st.session_state.quiz_score
                    st.session_state.onboarding_state["quiz_attempts"] = st.session_state.quiz_attempts_count
                    st.rerun() # This triggers the Excel generation node in graph.py
        else:
            st.error(f"❌ Score too low ({st.session_state.quiz_score}%). Attempt #{st.session_state.quiz_attempts_count} failed.")
            
            if st.button("🔄 Retry again"):
                # Clear keys for fresh quiz
                for key in ["quiz_questions", "quiz_submitted", "quiz_score", "quiz_passed"]:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()