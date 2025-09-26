from dotenv import load_dotenv
load_dotenv() 

import os
api_key = os.getenv("OPENAI_API_KEY")
from typing import Optional

from pypdf import PdfReader

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import ConversationalRetrievalChain


def _read_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    text = "\n".join(parts)
    if not text.strip():
        raise ValueError("No extractable text found (PDF might be scanned images).")
    return text


def get_chain(pdf_path: str) -> ConversationalRetrievalChain:
    # 1) read
    text = _read_pdf_text(pdf_path)


    # 2) chunk
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150,
        length_function=len
    )
    chunks = splitter.split_text(text)

    # 3) embeddings + vector store
    embeddings = OpenAIEmbeddings()  # uses OPENAI_API_KEY
    vectordb = FAISS.from_texts(chunks, embedding=embeddings)
    retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 4})

    # 4) LLM (chat model; davinci is retired)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 5) conversational RAG chain
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=False,
    )
    return chain
