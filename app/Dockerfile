# ใช้ Python เวอร์ชันใหม่และขนาดเล็ก
FROM python:3.11-slim

# ตั้ง timezone และ locale ให้ตรงไทย
ENV TZ=Asia/Bangkok

# ตั้ง working directory
WORKDIR /app

# ติดตั้ง dependency
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอก source code ทั้งหมด
COPY . .

# เปิดพอร์ตใน container
EXPOSE 5173

# ใช้ gunicorn (เหมาะกับ production)
RUN pip install gunicorn

# สั่งรัน Flask ผ่าน gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5173", "main:app"]
