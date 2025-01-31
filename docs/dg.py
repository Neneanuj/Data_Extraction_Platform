from diagrams import Cluster, Diagram, Edge
from diagrams.onprem.client import Users
from diagrams.programming.framework import FastAPI
from diagrams.programming.language import Python
from diagrams.generic.storage import Storage
from diagrams.onprem.network import Internet

with Diagram("Data Extraction Architecture", show=False, direction="LR"):
    users = Users("User Interface")
    web_sources = Internet("Web Sources")

    with Cluster("Application Stack"):
        with Cluster("Frontend"):
            streamlit = Python("Streamlit")

        with Cluster("Backend Services"):
            fastapi = FastAPI("FastAPI")

            with Cluster("Data Processing"):
                enterprise_pdf = Python("Enterprise PDF")
                open_source_pdf = Python("Open Source PDF")
                web_scraper = Python("Web Scraper")

            with Cluster("Standardization"):
                docling = Python("Docling")
                markitdown = Python("MarkItDown")

    storage = Storage("S3 Storage")

    # Bold connections using Edge
    users >> Edge(color="black", style="bold") >> streamlit
    streamlit >> Edge(color="black", style="bold") >> fastapi
    fastapi >> Edge(color="black", style="bold") >> [enterprise_pdf, open_source_pdf]
    web_sources >> Edge(color="black", style="bold") >> web_scraper
    fastapi >> Edge(color="black", style="bold") >> web_scraper
    [enterprise_pdf, open_source_pdf, web_scraper] >> Edge(color="black", style="bold") >> docling
    docling >> Edge(color="black", style="bold") >> markitdown
    markitdown >> Edge(color="black", style="bold") >> storage
    storage >> Edge(color="black", style="bold") >> streamlit
