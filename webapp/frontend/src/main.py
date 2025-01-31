import streamlit as st
import requests
import pandas as pd
import time
from io import BytesIO

import streamlit as st

# Page configuration
st.set_page_config(layout="wide", page_title="Data Extraction Tool")


# Initialize session state
if "api_response" not in st.session_state:
    st.session_state["api_response"] = {}

# Safely check for the "status" key
if "status" in st.session_state["api_response"]:
    if st.session_state["api_response"]["status"] == "success":
        st.write("Success!")
    else:
        st.write("Failure!")
else:
    st.write("Key 'status' not found in api_response.")


# FastAPI endpoint URL - update with your actual FastAPI server URL
API_BASE_URL = "http://127.0.0.1:8000"


# Sidebar navigation
with st.sidebar:
    st.title("Data Extraction Tool")
    page = st.radio("Select Operation:", 
                    ["Enterprise Extraction", 
                     "Open Source Extraction", 
                     "Web Scrape Tool"])

# Helper function for PDF upload and processing
def process_pdf(endpoint, file, bucket_name="bigdata-project1-storage"):
    files = {"file": file}
    data = {"bucket_name": bucket_name}
    try:
        response = requests.post(f"{API_BASE_URL}/{endpoint}", 
                               files=files, 
                               data=data)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Helper function for web scraping
def scrape_webpage(url, bucket_name="bigdata-project1-storage"):
    data = {"url": url, "bucket_name": bucket_name}
    try:
        response = requests.post(f"{API_BASE_URL}/scrape_webpage", 
                               data=data)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Main content area
if page == "Enterprise Extraction":
    st.title("Enterprise PDF Extraction")
    
    uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
    
    if uploaded_file:
        if st.button("Extract Data"):
            with st.spinner("Processing PDF..."):
                response = process_pdf("upload_pdf_enterprise", uploaded_file)
                st.session_state.api_response = response
                
        if st.session_state.api_response:
            if st.session_state.api_response["status"] == "success":
                st.success("Extraction Complete!")
                st.markdown(f"Download Link: {st.session_state.api_response['download_url']}")
            else:
                st.error(f"Error: {st.session_state.api_response['message']}")

elif page == "Open Source Extraction":
    st.title("Open Source PDF Extraction")
    
    uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
    
    if uploaded_file:
        if st.button("Extract Data"):
            with st.spinner("Processing PDF..."):
                response = process_pdf("upload_pdf_opensource", uploaded_file)
                st.session_state.api_response = response
                
        if st.session_state.api_response:
            if st.session_state.api_response["status"] == "success":
                st.success("Extraction Complete!")
                st.markdown(f"Download Link: {st.session_state.api_response['download_url']}")
            else:
                st.error(f"Error: {st.session_state.api_response['message']}")

else:  # Web Scrape Tool
    st.title("Web Scraping")
    
    url = st.text_input("Enter URL to scrape:", placeholder="https://example.com")
    
    if url:
        if st.button("Scrape Website"):
            with st.spinner("Scraping website..."):
                response = scrape_webpage(url)
                st.session_state.api_response = response
                
        if st.session_state.api_response is not None:

            if st.session_state.api_response.get("status") == "success":
                st.success("Scraping Complete!")
                st.markdown(f"Download Link: {st.session_state.api_response['download_url']}")
            else:
                st.error(f"Error: {st.session_state.api_response.get('message', 'Unknown error')}") 


# Footer
st.markdown("---")
st.markdown("Data Extraction Tool - v1.0")
