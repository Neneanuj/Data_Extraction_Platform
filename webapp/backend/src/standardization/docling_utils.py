from docling.document_converter import DocumentConverter

def docling_convert(source: str) -> str:
    """
    Convert a PDF (or URL) to a markdown text in a technical style using Docling.
    
    :param source: Path to a PDF file or a URL
    :return: Markdown text after conversion by Docling
    """
    converter = DocumentConverter()
    result = converter.convert(source)
    return result.document.export_to_markdown()
