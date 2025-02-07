FROM --platform=linux/amd64 python:3.12-slim

ENV ENV_MODE=production

# 1. 安装必要的系统依赖 (含 libyaml-dev)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    python3-dev \
    libssl-dev \
    libyaml-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libfreetype6-dev \
    libpq-dev \
    libopenjp2-7 \
    libpoppler-cpp-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# 2. 降级 setuptools 避免 cython_sources 问题
RUN pip install --no-cache-dir --upgrade pip setuptools==69.5.1 wheel

# 3. 先安装 Cython
RUN pip install --no-cache-dir Cython

# 4. 先单独安装 PyYAML 某个版本
RUN pip install --no-cache-dir PyYAML==6.0.2


# 5. 再安装其他依赖
RUN pip install --no-cache-dir -r requirements.txt

COPY webapp /app/webapp

WORKDIR /app/webapp/backend/src/api

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
