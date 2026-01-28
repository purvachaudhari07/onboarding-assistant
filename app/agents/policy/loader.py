import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

POLICY_PDF_PATH = os.path.join("data", "policies", "company_policy.pdf")

def load_policy_documents():
    loader = PyPDFLoader(POLICY_PDF_PATH)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    return splitter.split_documents(docs)

