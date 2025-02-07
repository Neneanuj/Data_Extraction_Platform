import streamlit as st
import requests
import pandas as pd
import time
from io import BytesIO

# Page configuration
st.set_page_config(layout="wide", page_title="Data Extraction Tool")

# Initialize session state
if "api_response" not in st.session_state:
    st.session_state["api_response"] = {}

# FastAPI endpoint URL - update with your actual FastAPI server URL
API_BASE_URL = "https://myapp-service-980441147674.us-east1.run.app"

# Sidebar navigation
with st.sidebar:
    st.title("Data Extraction Tool")
    page = st.radio("Select Operation:", 
                    ["Enterprise Extraction", 
                     "Open Source Extraction", 
                     "Web Scrape Tool",
                     "Diffbot Scraping"])

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
        response = requests.post(f"{API_BASE_URL}/scrape_webpage", data=data)
        return response.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}
if page == "Web Scrape Tool":
    st.title("Web Scraping")

    with st.form(key='url_form'):
        url = st.text_input("Enter URL to scrape:")
        submit_button = st.form_submit_button("Extract URL Data")

        if submit_button and url:
            with st.spinner("Scraping website..."):
                response = scrape_webpage(url)
                st.session_state.api_response = response

    # 🔹 Check if 'status' key exists before accessing it
    api_response = st.session_state.get("api_response", {})
    if "status" in api_response:
        if api_response["status"] == "success":
            st.success("Scraping Complete!")
            st.markdown(f"[Download Data]({api_response['download_url']})")
        else:
            st.error(f"Error: {api_response.get('message', 'Unknown error')}")
    else:
        st.error("Error: Invalid API response format.")

    # Clear results button
    if st.session_state.get("api_response") and st.button("Clear Results"):
        st.session_state.api_response = {}
        st.experimental_rerun()

# Helper function for Diffbot scraping
def scrape_diffbot(url, bucket_name="bigdata-project1-storage"):
    data = {"url": url, "bucket_name": bucket_name}
    try:
        response = requests.post(f"{API_BASE_URL}/scrape_diffbot", 
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
                
    if "status" in st.session_state.api_response:
        if st.session_state.api_response["status"] == "success":
            st.success("Extraction Complete!")
            st.markdown(f"Download Link: [Download]({st.session_state.api_response['download_url']})")
        else:
            st.error(f"Error: {st.session_state.api_response.get('message', 'Unknown error')}")
    elif st.session_state.api_response:
        st.error("Key 'status' not found in api_response.")

elif page == "Open Source Extraction":
    st.title("Open Source PDF Extraction")
    
    uploaded_file = st.file_uploader("Upload PDF file", type="pdf")
    
    if uploaded_file:
        if st.button("Extract Data"):
            with st.spinner("Processing PDF..."):
                response = process_pdf("upload_pdf_opensource", uploaded_file)
                st.session_state.api_response = response
                
    if "status" in st.session_state.api_response:
        if st.session_state.api_response["status"] == "success":
            st.success("Extraction Complete!")
            st.markdown(f"Download Link: [Download]({st.session_state.api_response['download_url']})")
        else:
            st.error(f"Error: {st.session_state.api_response.get('message', 'Unknown error')}")
    elif st.session_state.api_response:
        st.error("Key 'status' not found in api_response.")

elif page == "Web Scrape Tool":
    st.title("Web Scraping")
    
    with st.form(key='web_scrape_form'):  
        url = st.text_input("Enter URL to scrape:", placeholder="https://example.com")
        submit_button = st.form_submit_button("Extract URL Data")
        
        if submit_button and url:
            with st.spinner("Scraping website..."):
                response = scrape_webpage(url)
                st.session_state.api_response = response
                
    if "status" in st.session_state.api_response:
        if st.session_state.api_response["status"] == "success":
            st.success("Scraping Complete!")
            st.markdown(f"Download Link: [Download]({st.session_state.api_response['download_url']})")
        else:
            st.error(f"Error: {st.session_state.api_response.get('message', 'Unknown error')}")
    elif st.session_state.api_response:
        st.error("Key 'status' not found in api_response.")
    

    if st.session_state.get('api_response') and st.button("Clear Results", use_container_width=True):
        st.session_state.api_response = {}
        st.experimental_rerun()

elif page == "Diffbot Scraping":
    st.title("Diffbot Web Scraping")
    
    # Use a form to capture Enter key press
    with st.form(key='diffbot_form'):
        url = st.text_input("Enter URL to scrape with Diffbot and press Enter:", placeholder="https://example.com")
        submit_button = st.form_submit_button("Scrape with Diffbot")
        
        if submit_button and url:
            with st.spinner("Scraping website with Diffbot..."):
                response = scrape_diffbot(url)
                st.session_state.api_response = response
                
    if "status" in st.session_state.api_response:
        if st.session_state.api_response["status"] == "success":
            st.success("Scraping Complete!")
            st.markdown(f"Download Link: [Download]({st.session_state.api_response['download_url']})")
        else:
            st.error(f"Error: {st.session_state.api_response.get('message', 'Unknown error')}")
    elif st.session_state.api_response:
        st.error("Key 'status' not found in api_response.")
    
    # Clear results button (outside the form)
    if st.session_state.get('api_response') and st.button("Clear Results", use_container_width=True):
        st.session_state.api_response = {}
        st.experimental_rerun()

# Footer
st.markdown("---")
st.markdown("Data Extraction Tool - v1.0")
