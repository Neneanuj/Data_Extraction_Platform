from docling.document_converter import DocumentConverter

def docling_convert(source: str) -> str:
    """
    使用Docling将PDF(或URL)转换为技术风格的Markdown文本。
    
    :param source: PDF文件路径或URL
    :return: Docling转换后的Markdown文本
    """
    converter = DocumentConverter()
    result = converter.convert(source)
    return result.document.export_to_markdown()
