FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# browser_data 通过 volume 挂载持久化登录态
EXPOSE 3459

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3459"]
