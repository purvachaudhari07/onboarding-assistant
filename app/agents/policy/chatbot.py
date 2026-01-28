import streamlit as st
import os

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from app.agents.policy.loader import load_policy_documents
from app.agents.policy.vectorstore import create_vector_store


def policy_chatbot_ui():
    st.subheader("💬 Policy Chatbot")

    if "rag_chain" not in st.session_state:

        # 1️⃣ Load policy documents
        docs = load_policy_documents()

        # 2️⃣ Create vector store
        vectordb = create_vector_store(docs)
        retriever = vectordb.as_retriever(search_kwargs={"k": 3})

        # 3️⃣ Groq LLM
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=st.secrets["GROQ_API_KEY"]
        )

        # 4️⃣ Prompt
        prompt = ChatPromptTemplate.from_template(
            """
            You are an HR onboarding assistant.
            Answer ONLY using the provided company policy context.
            If the answer is not present, say:
            "This information is not mentioned in the policy."

            Context:
            {context}

            Question:
            {question}
            """
        )

        # 5️⃣ RAG chain (modern LangChain LCEL)
        st.session_state.rag_chain = (
            {
                "context": retriever,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )

    question = st.text_input("Ask a question from company policy")

    if st.button("Ask"):
        if question.strip() == "":
            st.warning("Please enter a question")
        else:
            answer = st.session_state.rag_chain.invoke(question)
        
        # st.success(answer)  
        
        # New Technique
        st.markdown(f"""
            <div class="chatbot-response-box">
                {answer}
            </div>
        """, unsafe_allow_html=True)
