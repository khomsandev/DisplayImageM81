from fastapi import FastAPI, HTTPException, Response
import requests
from datetime import datetime
import uuid
import base64
import logging

app = FastAPI(title="MFlow View API", version="1.0.1")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 🔹 API URLs
TOKEN_URL = "https://uat-spf.mflowthai.com/authservice/api/v1/auth"
IMAGE_URL = "https://uat-spf.mflowthai.com/file-service/api/v1/download"

# 🔹 Credentials
USERNAME = "thapana.ch@appworks.co.th"
PASSWORD = "Mflow1234"

# 🔹 API Key
API_KEY = "JDJ5JDEwJElrcExEY1JvVERJSnVmZ254VkVpSE9HOGdBM2p5R3dXbDMySXNkb1V5QjV2Q0c5YWQxaVlP"

# 🔹 Base Headers (ใช้กับทุก API)
BASE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,th;q=0.8",
    "AccountType": "ADMIN",
    "Connection": "keep-alive",
    "Language": "TH",
    "LoginType": "NORMAL",
    "Origin": "http://172.17.40.68:8000",
    "Referer": "http://172.17.40.68:8000/admin/allinone/detail",
    "Source": "ADMIN",
    "System": "M00000",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/131.0.0.0 Safari/537.36"
}

# ✅ เพิ่ม apikey ใน header ตอนขอ token
def get_token():
    headers = BASE_HEADERS.copy()
    headers["apikey"] = API_KEY
    headers["RequestDate"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
    headers["TransactionId"] = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4().int)[:6]}"

    try:
        logging.info("🔐 Requesting access token with Basic Auth + API key...")
        r = requests.post(TOKEN_URL, headers=headers, auth=(USERNAME, PASSWORD), timeout=10)
        logging.info(f"Token response: {r.status_code}")
        data = r.json()
        logging.info("✅ Token response JSON: %s", data)

        token = data.get("accessToken") or data.get("access_token") or data.get("token")
        if not token:
            logging.error("❌ Token not found in response: %s", data)
            raise HTTPException(status_code=500, detail="Token not found in response")
        logging.info("🔑 Got token (truncated): %s...", token[:40])
        return token
    except Exception as e:
        logging.error("❌ Token request failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Token request failed: {e}")

# 🔹 Header generator (ใช้หลังจากมี token แล้ว)
def gen_headers(token: str):
    headers = BASE_HEADERS.copy()
    headers.update({
        "Authorization": f"Bearer {token}",
        "RequestDate": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
        "TransactionId": f"T{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4().int)[:6]}",
        "apikey": API_KEY
    })
    return headers

# 🔹 ดึงภาพจาก file-service
@app.get("/img/{file_id}")
def get_image(file_id: str):
    token = get_token()
    headers = gen_headers(token)

    try:
        files = {"filesId": (None, file_id)}  # multipart/form-data
        res = requests.post(IMAGE_URL, headers=headers, files=files, timeout=30)

        logging.info(f"📸 Image response: {res.status_code}")

        if res.status_code != 200:
            logging.error("❌ Image request failed: %s", res.text[:300])
            raise HTTPException(status_code=res.status_code, detail=res.text)

        content_type = res.headers.get("Content-Type", "")
        filename = f"{file_id}.jpg"

        # ✅ ถ้าเป็น binary image
        if "image" in content_type or "octet-stream" in content_type:
            return Response(
                res.content,
                media_type=content_type or "image/jpeg",
                headers={"Content-Disposition": f'inline; filename="{filename}"'}
            )

        # ✅ ถ้าเป็น JSON base64
        data = res.json()
        content = (
            data.get("content")
            or data.get("image_base64")
            or data.get("data", {}).get("content")
            or data.get("data", {}).get("fileContent")
        )

        if not content:
            raise HTTPException(status_code=404, detail="Image content not found")

        if content.startswith("data:image"):
            content = content.split(",")[1]

        return Response(
            base64.b64decode(content),
            media_type="image/jpeg",
            headers={"Content-Disposition": f'inline; filename="{filename}"'}
        )

    except Exception as e:
        logging.error("❌ Image request failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Image request failed: {e}")
