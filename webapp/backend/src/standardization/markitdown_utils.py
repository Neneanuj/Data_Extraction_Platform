from markitdown import MarkItDown

def markitdown_convert(file_path: str) -> str:
    """
    Convert a file (such as .xlsx or .pdf) into Markdown text using MarkItDown.
    
    :param file_path: The path to the file
    :return: Markdown text after conversion by MarkItDown
    """
    md = MarkItDown()
    result = md.convert(file_path)
    return result.text_content
