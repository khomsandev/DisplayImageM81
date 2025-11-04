import os
import io
from functools import lru_cache
from datetime import datetime
from flask import Flask, Response, render_template_string, request, abort
import requests
from dotenv import load_dotenv
from cachetools import TTLCache
import time

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL")
API_AUTH_BEARER = os.getenv("API_AUTH_BEARER")
API_KEY = os.getenv("API_KEY")
API_HOST = os.getenv("API_HOST")

app = Flask(__name__)

def _api_headers():
    return {
        "TransactionId": "T20190130123001000001",
        "RequestDate": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3],
        "Source": "ADMIN",
        "System": "M00000",
        "Language": "TH",
        "ApiKey": API_KEY,
        "Authorization": f"Bearer {API_AUTH_BEARER}",
        **({"Host": API_HOST} if API_HOST else {}),
    }

def fetch_file_bytes(file_id: str):
    """
    ส่ง multipart/form-data: filesId=<id>
    ใช้ requests 'files' เพื่อให้เป็น multipart เหมือน curl --form
    """
    try:
        resp = requests.post(
            API_BASE_URL,
            headers=_api_headers(),
            files={"filesId": (None, file_id)},
            timeout=60,
        )
    except requests.RequestException as e:
        raise RuntimeError(f"request error: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    content_type = resp.headers.get("Content-Type", "")
    return resp.content, content_type or "application/octet-stream"

@lru_cache(maxsize=256)
def get_image_cached(file_id: str):
    # แคชในหน่วยความจำ ลดโหลดกับ backend
    data, ctype = fetch_file_bytes(file_id)
    return data, ctype

@app.route("/")
def index():
    """
    เปิดด้วย:
      /?ids=uuid1,uuid2,uuid3
    ถ้าไม่ส่ง ids จะใส่ตัวอย่างให้
    """
    ids_param = request.args.get("ids", "")
    if not ids_param.strip():
        # ตัวอย่าง (ใส่ ids ของคุณเอง)
        ids = [
            "30dad974-35fb-465f-b8cd-32fe87ce255a",
            # "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            # "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy",
        ]
    else:
        ids = [x.strip() for x in ids_param.split(",") if x.strip()]

    html = """
    <!doctype html>
<html lang="th">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Image Gallery</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; }
    h1 { margin: 0 0 16px 0; }
    .hint { color: #666; margin-bottom: 20px; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 16px;
    }
    .card {
      border: 1px solid #e5e5e5;
      border-radius: 12px;
      padding: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
      background: #fff;
    }
    /* ทำให้รูปชัดเจนว่า “กดเพื่อขยาย” */
    .card img {
      width: 100%;
      height: 220px;
      object-fit: contain;
      background: #fafafa;
      border-radius: 8px;
      cursor: zoom-in;           /* <- เพิ่ม */
    }
    /* ใช้กับ lightbox */
    .img-thumb { max-width: 100%; }
    .lb-backdrop{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:9999}
    .lb-backdrop.show{display:flex}
    .lb-img{max-width:90vw;max-height:90vh;transform-origin:center center;transition:transform .1s ease-out;cursor:grab;border-radius:12px}
    .lb-close{position:fixed;top:16px;right:20px;font-size:24px;color:#fff;cursor:pointer}

    .id { font-size: 12px; color: #555; margin-top: 8px; word-break: break-all; }
    .toolbar { margin-bottom: 12px; }
    input[type=text] {
      width: min(820px, 90vw);
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid #ddd;
    }
    button {
      padding: 8px 14px; border: 0; border-radius: 8px; cursor: pointer; margin-left: 8px;
      background: #111; color: #fff;
    }
    @media (prefers-color-scheme: dark) {
      body { background: #0b0b0b; color: #e8e8e8; }
      .card { background: #111; border-color: #222; box-shadow: none; }
      .hint { color: #aaa; }
      input[type=text]{ background: #111; color: #e8e8e8; border-color: #222; }
      button{ background: #e8e8e8; color: #111; }
    }
  </style>
</head>
<body>
  <h1>Image Gallery</h1>
  <div class="hint">ใส่หลาย <code>filesId</code> คั่นด้วยเครื่องหมายจุลภาค แล้วกด View</div>
  <form class="toolbar" method="get" action="/">
    <input type="text" name="ids" placeholder="uuid1,uuid2,uuid3" value="{{ ids_text }}">
    <button type="submit">View</button>
  </form>

  <div class="grid">
    {% for fid in ids %}
      <div class="card">
        <!-- เพิ่ม class="img-thumb" เพื่อ hook lightbox -->
        <img class="img-thumb"
             src="/img/{{ fid }}"
             alt="image {{ fid }}"
             onerror="this.src='data:image/svg+xml;utf8,<svg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'400\\' height=\\'220\\'><rect width=\\'100%\\' height=\\'100%\\' fill=\\'%23f0f0f0\\'/><text x=\\'50%\\' y=\\'50%\\' dominant-baseline=\\'middle\\' text-anchor=\\'middle\\' fill=\\'%23999\\' font-family=\\'sans-serif\\' font-size=\\'14\\'>Load error</text></svg>';">
        <div class="id">{{ fid }}</div>
      </div>
    {% endfor %}
  </div>

  <!-- Lightbox Markup -->
  <div class="lb-backdrop" id="lb" aria-hidden="true">
    <span class="lb-close" id="lbClose" aria-label="Close">✕</span>
    <img class="lb-img" id="lbImg" src="" alt="zoom">
  </div>

  <!-- Lightbox Script -->
  <script>
  (function(){
    const lb = document.getElementById('lb');
    const img = document.getElementById('lbImg');
    const closeBtn = document.getElementById('lbClose');

    let scale = 1, isPanning = false, startX=0, startY=0, translateX=0, translateY=0, baseScale=1, baseTX=0, baseTY=0, touchDist=0, startMid={x:0,y:0};

    function apply(){ img.style.transform = `translate(${translateX}px,${translateY}px) scale(${scale})`; }
    function reset(){ scale=1; translateX=0; translateY=0; apply(); }
    function open(src, alt){
      img.src = src; img.alt = alt || 'zoom';
      reset(); lb.classList.add('show'); document.body.style.overflow='hidden';
    }
    function close(){
      lb.classList.remove('show'); document.body.style.overflow='';
      // ป้องกันภาพค้างโหลดขณะปิด (optional)
      // setTimeout(()=>{ img.src=''; },150);
    }

    // Delegate click จากรูปทุกใบ
    document.addEventListener('click', (e)=>{
      const t = e.target;
      if(t && t.classList && t.classList.contains('img-thumb')){
        e.preventDefault();
        open(t.getAttribute('src'), t.getAttribute('alt'));
      }
    });

    // ปิดเมื่อคลิกพื้นหลัง/ปุ่ม X/กด ESC
    closeBtn.addEventListener('click', close);
    lb.addEventListener('click', e => { if(e.target === lb) close(); });
    window.addEventListener('keydown', e => { if(e.key === 'Escape' && lb.classList.contains('show')) close(); });

    // wheel zoom (desktop)
    img.addEventListener('wheel', e => {
      e.preventDefault();
      const delta = -Math.sign(e.deltaY)*0.2;
      const prev = scale;
      scale = Math.min(6, Math.max(1, scale + delta));
      const rect = img.getBoundingClientRect();
      const mx = e.clientX - rect.left, my = e.clientY - rect.top;
      translateX -= (mx - rect.width/2)/prev * (scale - prev);
      translateY -= (my - rect.height/2)/prev * (scale - prev);
      apply();
    }, {passive:false});

    // pan (desktop)
    img.addEventListener('mousedown', e => { isPanning=true; startX=e.clientX-translateX; startY=e.clientY-translateY; img.style.cursor='grabbing'; });
    window.addEventListener('mouseup', ()=>{ isPanning=false; img.style.cursor='grab'; });
    window.addEventListener('mousemove', e => { if(!isPanning) return; translateX=e.clientX-startX; translateY=e.clientY-startY; apply(); });

    // touch pinch-zoom + pan (mobile)
    const dist = (a,b)=> Math.hypot(a.clientX-b.clientX, a.clientY-b.clientY);
    lb.addEventListener('touchstart', e=>{
      if(e.touches.length===2){
        touchDist = dist(e.touches[0], e.touches[1]);
        baseScale = scale; baseTX=translateX; baseTY=translateY;
        startMid = {x:(e.touches[0].clientX+e.touches[1].clientX)/2, y:(e.touches[0].clientY+e.touches[1].clientY)/2};
      }
    }, {passive:true});
    lb.addEventListener('touchmove', e=>{
      if(e.touches.length===2){
        e.preventDefault();
        const d = dist(e.touches[0], e.touches[1]);
        scale = Math.min(6, Math.max(1, baseScale * (d/touchDist)));
        const mid = {x:(e.touches[0].clientX+e.touches[1].clientX)/2, y:(e.touches[0].clientY+e.touches[1].clientY)/2};
        translateX = baseTX + (mid.x-startMid.x);
        translateY = baseTY + (mid.y-startMid.y);
        apply();
      }
    }, {passive:false});
  })();
  </script>
</body>
</html>

    """
    return render_template_string(html, ids=ids, ids_text=",".join(ids))

@app.route("/img/<path:file_id>")
def image_proxy(file_id: str):
    try:
        data, ctype = get_image_cached(file_id)
    except Exception as e:
        # ถ้า error ลองไม่ใช้แคชเพื่อรีเฟรช
        try:
            get_image_cached.cache_clear()
            data, ctype = get_image_cached(file_id)
        except Exception as e2:
            abort(502, description=f"Fetch failed: {e2}")


    return Response(data, mimetype=ctype or "image/jpeg")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5173, debug=True)
