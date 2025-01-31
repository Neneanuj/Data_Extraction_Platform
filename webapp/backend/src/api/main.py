import os
import sys
import tempfile
import zipfile
import io
import shutil
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi import FastAPI, File, UploadFile, Form,HTTPException
import uvicorn
import tempfile
from typing import Dict, Any
from S3.s3_organization import upload_to_s3, generate_s3_key,generate_presigned_url
from extraction.pdf_parser_enterprise import extract_and_store_pdf
from extraction.pdf_parser_opensource import process_pdf_with_open_source
from extraction.web_scraper import scrape_url_and_convert

app = FastAPI()
print(os.path.abspath(__file__))

@app.post("/upload_pdf_enterprise")
async def process_pdf(
    file: UploadFile = File(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:
    try:
        # 临时保存上传的 PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # 上传到 S3 原始存储
        s3_key = generate_s3_key(file_type="pdf", file_name=file.filename)
        upload_to_s3(bucket_name, s3_key, tmp_path)

        # 调用处理函数（不再需要传递 base_key）
        result = extract_and_store_pdf(pdf_path=s3_key, bucket_name=bucket_name)

        # 清理临时文件
        os.remove(tmp_path)

        return {
            "status": "success",
            "download_url": result["download_url"],
            "message": "数据已按规则存储到 S3，可通过链接下载完整 ZIP 文件"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}



@app.post("/upload_pdf_opensource")
async def upload_pdf_opensource(
    file: UploadFile = File(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:

    # 1. 把上传的 PDF 存到临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
        content = await file.read()
        tmp_pdf.write(content)
        pdf_path = tmp_pdf.name

    # 2. 调用解析函数 -> 得到两个 md 文本 + images_dir + tables_dir
    parsed = process_pdf_with_open_source(pdf_path)

    # 3. 创建内存Zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 两个 Markdown
        zf.writestr("docling.md", parsed["docling_markdown"])
        zf.writestr("markitdown.md", parsed["markitdown_markdown"])

        # 图片目录
        if os.path.exists(parsed["images_dir"]):
            for root, _, files in os.walk(parsed["images_dir"]):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    zip_path = os.path.join("images", file_name)
                    zf.write(file_path, zip_path)

        # 表格目录
        if os.path.exists(parsed["tables_dir"]):
            for root, _, files in os.walk(parsed["tables_dir"]):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    zip_path = os.path.join("tables", file_name)
                    zf.write(file_path, zip_path)

    # 4. 清理临时目录/文件
    os.remove(pdf_path)
    shutil.rmtree(parsed["images_dir"], ignore_errors=True)
    shutil.rmtree(parsed["tables_dir"], ignore_errors=True)

    # 5. 上传Zip到S3
    zip_key = generate_s3_key("pdf/opensource", file.filename) + "_result.zip"
    zip_buffer.seek(0)
    upload_to_s3(bucket_name, zip_key, zip_buffer.getvalue())

    # 6. 返回预签名下载链接
    download_url = generate_presigned_url(bucket_name, zip_key)
    return {
        "status": "success",
        "download_url": download_url,
        "message": "ZIP包含两个Markdown文本、以及提取到的图片、表格。"
    }


@app.post("/scrape_webpage")
async def scrape_webpage(
    url: str = Form(...),
    bucket_name: str = Form(default="bigdata-project1-storage")
) -> Dict[str, Any]:
    """
    1) 爬取网页, 提取文本/图片/表格/链接
    2) 转换成 docling.md, markitdown.md
    3) 打包并上传到S3
    """
    # 1. 调用爬虫 + 转换函数
    result = scrape_url_and_convert(url)
    if result["error"]:
        return {"status": "error", "message": result["error"]}

    docling_md = result["docling_markdown"]
    markitdown_md = result["markitdown_markdown"]
    text_raw = result["text_raw"]
    images_data = result["images"]  # 列表[dict, dict...]
    tables_data = result["tables"]  # 列表 [DataFrame1, DF2...]
    urls_data = result["urls"]      # 列表[dict, dict...]

    # 2. 创建内存 ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # (a) 写入两个 Markdown
        zf.writestr("docling.md", docling_md)
        zf.writestr("markitdown.md", markitdown_md)

        # (b) 可选，写入原始文本 content.txt
        zf.writestr("content.txt", text_raw)

        # (c) 如果需要把提取的表格 DataFrame 导出到 tables/*.csv
        if tables_data:
            for i, df in enumerate(tables_data, start=1):
                csv_name = f"tables/table_{i}.csv"
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                zf.writestr(csv_name, csv_buffer.getvalue())
        else:
            # 如果想强制出现一个空tables/文件夹，可放一个占位文件
            zf.writestr("tables/.placeholder", "")

        # (d) 如果只想保存图片元数据成一个CSV, 放到 images/images_metadata.csv
        if images_data:
            df_images = pd.DataFrame(images_data)
            csv_buf = io.StringIO()
            df_images.to_csv(csv_buf, index=False)
            zf.writestr("images/images_metadata.csv", csv_buf.getvalue())
        else:
            # 同理占位文件
            zf.writestr("images/.placeholder", "")

        # (e) 如果想保存所有<a>链接信息成一个CSV
        if urls_data:
            df_urls = pd.DataFrame(urls_data)
            csv_buf = io.StringIO()
            df_urls.to_csv(csv_buf, index=False)
            zf.writestr("urls/urls_metadata.csv", csv_buf.getvalue())
        else:
            zf.writestr("urls/.placeholder", "")

        # (f) 如果想要**实际下载网页上所有图片**到 images/ 目录
        #     可以再写一段逻辑:
        #
        # for i, img_info in enumerate(images_data, start=1):
        #     img_url = img_info["src"]
        #     try:
        #         r = requests.get(img_url, timeout=10)
        #         if r.status_code == 200:
        #             # 推断文件后缀
        #             ext = os.path.splitext(img_url)[1]
        #             if not ext:
        #                 ext = ".jpg"
        #             file_name = f"images/image_{i}{ext}"
        #             zf.writestr(file_name, r.content)
        #     except:
        #         pass
        #
        # 这样就真的把远程图片也打包进 ZIP 了。
        # 不过可能比较慢&大，所以酌情使用。

    # 3. 上传到S3
    zip_key = generate_s3_key("web_scraper", "result") + ".zip"
    zip_buffer.seek(0)
    upload_to_s3(bucket_name, zip_key, zip_buffer.getvalue())

    # 4. 返回下载链接
    download_url = generate_presigned_url(bucket_name, zip_key)
    return {
        "status": "success",
        "download_url": download_url,
        "message": "Zip 包含 docling.md, markitdown.md, content.txt, images/tables/urls 元数据等"
    }

# 其他 endpoint ...
# 比如你的 /upload_pdf_opensource, /upload_pdf_enterprise 等

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)