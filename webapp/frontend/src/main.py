import streamlit as st
import requests
import pandas as pd
import time
from io import BytesIO

# Initialize session state
if 'api_response' not in st.session_state:
    st.session_state.api_response = None

# FastAPI endpoint URL - update with your actual FastAPI server URL
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(layout="wide", page_title="Data Extraction Tool")

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
    
    # Use a form to capture Enter key press
    with st.form(key='url_form'):
        url = st.text_input("Enter URL to scrape and press Enter:", placeholder="https://example.com")
        submit_button = st.form_submit_button("Extract URL Data")
        
        if submit_button and url:
            try:
                with st.spinner("Scraping website..."):
                    response = scrape_webpage(url)
                    st.session_state.api_response = response
                    
                if st.session_state.api_response:
                    if st.session_state.api_response["status"] == "success":
                        st.success("Scraping Complete!")
                        st.markdown(f"Download Link: {st.session_state.api_response['download_url']}")
                    else:
                        st.error(f"Error: {st.session_state.api_response['message']}")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Clear results button (outside the form)
    if st.session_state.get('api_response') and st.button("Clear Results", use_container_width=True):
        st.session_state.api_response = None
        st.experimental_rerun()



# Footer
st.markdown("---")
st.markdown("Data Extraction Tool - v1.0")
