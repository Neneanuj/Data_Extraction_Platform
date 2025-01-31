from markitdown import MarkItDown

def markitdown_convert(file_path: str) -> str:
    """
    使用MarkItDown将文件(如.xslx或.pdf)转换为Markdown文本。
    
    :param file_path: 文件路径
    :return: MarkItDown转换后的Markdown文本
    """
    md = MarkItDown()
    result = md.convert(file_path)
    return result.text_content
