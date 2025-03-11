import streamlit as st
import fitz  # PyMuPDF for PDF extraction
import pymongo
import re

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["resume_db"]
collection = db["resumes"]

# Extract text from PDF
def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    return " ".join(page.get_text("text") for page in doc)

# Extract name using regex
def extract_name(text):
    pattern = r"\b[A-Z][a-z]+\s[A-Z][a-z]+\b"
    match = re.findall(pattern, text)
    return match[0] if match else "Not Found"

# Extract email using regex
def extract_email(text):
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    match = re.findall(pattern, text)
    return match if match else "Not Found"

# Extract phone number using regex
def extract_phone(text):
    pattern = r"\b\d{10}\b"
    match = re.findall(pattern, text)
    return match if match else "Not Found"

# ATS Checker (Keyword Matching)
def ats_score(text, job_keywords):
    text = text.lower()
    job_keywords = [kw.lower() for kw in job_keywords]
    matched_keywords = [kw for kw in job_keywords if kw in text]
    score = (len(matched_keywords) / len(job_keywords)) * 100 if job_keywords else 0
    return round(score, 2), matched_keywords

# Process and store resume
def process_resume(file, job_keywords):
    text = extract_text(file)
    score, matched_keywords = ats_score(text, job_keywords)
    data = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "text": text,
        "ats_score": score,
        "matched_keywords": matched_keywords
    }
    collection.insert_one(data)
    return data

# Streamlit UI
st.title("📄 Resume Parser & ATS Checker")
st.write("Upload a PDF resume, extract details, and check its ATS score based on job keywords.")

uploaded_file = st.file_uploader("Upload Resume (PDF only)", type=["pdf"])
job_keywords = st.text_area("Enter job-related keywords (comma-separated)").split(",")

if uploaded_file is not None and job_keywords:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    resume_data = process_resume("temp.pdf", job_keywords)
    
    st.subheader("Extracted Details")
    st.write(f"**Name:** {resume_data['name']}")
    st.write(f"**Email:** {', '.join(resume_data['email'])}")
    st.write(f"**Phone:** {', '.join(resume_data['phone'])}")
    
    st.subheader("ATS Score")
    st.write(f"**Match Score:** {resume_data['ats_score']}%")
    st.write(f"**Matched Keywords:** {', '.join(resume_data['matched_keywords'])}")
    
    st.success("✅ Resume processed and stored in MongoDB!")



