# AI-Powered Document Processing System 
### **📄 Project Summary**  
Demo Link: https://youtu.be/EA8dEzMJPnM

🚀 **Extract, Standardize, and Store Data from PDFs and Webpages**  

## **📌 Overview**
This project is an **AI-powered document processing system** that extracts, standardizes, and stores data from **PDFs and webpages**. It uses **open-source tools** (PyPDF2, pdfplumber, BeautifulSoup) and an **enterprise service** (Microsoft Document Intelligence) to process unstructured data. Extracted content is standardized into **Markdown format** using **Docling and MarkItDown** and stored in **AWS S3** for retrieval.  

The system provides:  
✅ **FastAPI backend** for document processing  
✅ **Streamlit web interface** for user-friendly interaction  
✅ **Cloud storage (AWS S3)** for processed files  

---

## **🔑 Features**
✅ **Extract text, images, charts, and tables** from PDFs & webpages  
✅ **Use AI-powered document processing** (Microsoft Document Intelligence)  
✅ **Compare Open-Source vs. Enterprise tools** for text extraction  
✅ **Standardize extracted content** into Markdown using **Docling & MarkItDown**  
✅ **Store processed files in AWS S3** for easy retrieval  
✅ **Provide an API with FastAPI** for seamless integration  
✅ **User-friendly Streamlit Web App** to upload and process files  

---

## **✔ Technology Stack**

| **Category**       | **Tools Used** |
|------------------|--------------|
| **Programming Language** | Python 3.8+ |
| **PDF Processing** | PyPDF2, pdfplumber, Microsoft Document Intelligence |
| **Web Scraping** | BeautifulSoup, requests |
| **Markdown Standardization** | Docling, MarkItDown |
| **Backend API** | FastAPI |
| **Frontend UI** | Streamlit |
| **Cloud Storage** | AWS S3 |
| **Deployment** | Render, Streamlit Cloud |

---

## **🛠️ Diagrams**

![image](./docs/data_extraction_architecture.png)


---

## **🛠️ User Guide**
1. Users can choose different ways to extract data. 
2. When user inputs a PDF or URL, it will be temporarily stored in S3 first
3. PDF data will be processed through the API call function to obtain the table image and text
4. Text will be marked down in two ways (docling markitdown)
5. Finally a **download link** will be returned, which contains all the output files.

---

## **📂 Project Structure**
```plaintext
├.
├── .github
│   └── workflows          # CI/CD automation setup
├── docs
│   └── Codelab.md         # Project documentation
├── webapp
│   ├── frontend           # Streamlit frontend for user interaction
│   │   └── src
│   │       └── main.py    # Frontend entry point
│   └── backend
│       └── src
│           ├── S3
│           │   ├── __init__.py
│           │   └── s3_organization.py
│           ├── api           # FastAPI backend
│           │   ├── __init__.py
│           │   └── main.py   # FastAPI entry point
│           ├── extraction    # Extract data from PDFs & webpages
│           │   ├── __init__.py
│           │   ├── pdf_parser_enterprise.py    # PDF extraction using Microsoft Document Intelligence
│           │   ├── pdf_parser_opensource.py    # PDF extraction using PyPDF2, pdfplumber
│           │   └── web_scraper.py              # Web scraping using BeautifulSoup
│           └── standardization                 # Standardization using Docling & MarkItDown
│               ├── __init__.py
│               ├── docling_utils.py
│               └── markitdown_utils.py
├── .gitignore            # Git ignore file
├── AiuseDisclosure.md    # AI usage disclosure
├── README.md             # Project documentation
└── ToolsComparison.md    # Tools comparison documentation

```

---

## **🚀 Installation & Setup**
1️⃣ Prerequisites
Ensure you have:

Python 3.8 or higher
pip (Python package manager)
AWS credentials (if storing files in AWS S3)

2️⃣ Clone the Repository
```
git clone https://github.com/Neneanuj/BigData_Labs.git
cd BigData_Labs
```

3️⃣ Create a Virtual Environment
```
python -m venv env
source env/bin/activate  # macOS/Linux
env\Scripts\activate     # Windows
```
---

## **🛠️ Usage**

1️⃣ Run the FastAPI Backend
```
uvicorn src.api.main:app --reload
```
API will be available at:
🔗 http://127.0.0.1:8000/docs

2️⃣ Run the Streamlit App
```
streamlit run src/streamlit_app/app.py
```

App will open at:
🔗 http://localhost:8501

3️⃣ Upload a File or Webpage
* Upload a PDF file or enter a webpage URL in the Streamlit app.
* The API processes the document and returns standardized Markdown output.
* Extracted content is stored in AWS S3 (if enabled).

---

## **📌 Expected Outcomes**

* A functional AI-powered document processing system for extracting and standardizing data.
* A working API & Streamlit app that allow users to process PDFs & webpages.  
* A performance comparison between open-source and enterprise extraction tools.  
* A fully documented project with findings, code, and usage guidelines.  

---

## **📌 AI Use Disclosure**
This project uses:

* Microsoft Document Intelligence for enterprise PDF processing.
* Docling & MarkItDown for text standardization.
* AWS S3 for cloud storage.
📄 See AiUseDisclosure.md for details.

---

## **👨‍💻 Authors**
* Sicheng Bao (@Jellysillyfish13)
* Yung Rou Ko (@KoYungRou)
* Anuj Rajendraprasad Nene (@Neneanuj)

---

## **📞 Contact**
For questions, reach out via Big Data Course or open an issue on GitHub.
