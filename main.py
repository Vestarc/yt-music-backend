import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Небольшой кэш в памяти, чтобы бесплатный сервер не перегружался
CACHE = {}


def cache_get(key):
    item = CACHE.get(key)
    if item and item[0] > time.time():
        return item[1]
    return None


def cache_set(key, value, ttl):
    CACHE[key] = (time.time() + ttl, value)
    if len(CACHE) > 300:
        for k in list(CACHE)[:100]:
            CACHE.pop(k, None)


def get_thumbnail(entry):
    thumb = entry.get("thumbnail")
    if not thumb and entry.get("thumbnails"):
        thumbs = entry.get("thumbnails")
        if isinstance(thumbs, list) and len(thumbs) > 0:
            thumb = thumbs[-1].get("url")
    return [{"url": thumb or ""}]


def sc_search(query, n, fallback_artist="SoundCloud"):
    opts = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "socket_timeout": 15,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(f"scsearch{n}:{query}", download=False)

    results, seen = [], set()
    for entry in (info or {}).get("entries") or []:
        if not entry:
            continue
        url = entry.get("url") or entry.get("webpage_url")
        if not url or url in seen:
            continue
        seen.add(url)
        results.append({
            "videoId": url,
            "title": entry.get("title") or "Unknown Title",
            "artists": [{"name": entry.get("uploader") or entry.get("artist") or fallback_artist}],
            "thumbnails": get_thumbnail(entry),
            "source": "SoundCloud",
        })
    return results


@app.get("/")
def root():
    return {"status": "YouMusic Core Engine Running"}


@app.get("/search")
def search(q: str, n: int = 30):
    n = max(5, min(n, 50))
    key = f"s:{q.lower()}:{n}"
    cached = cache_get(key)
    if cached is not None:
        return cached
    try:
        results = sc_search(q, n)
    except Exception:
        results = []
    if results:
        cache_set(key, results, 600)
    return results


@app.get("/charts")
def charts():
    cached = cache_get("charts")
    if cached is not None:
        return cached
    try:
        tracks = sc_search("global top hits", 40, "SoundCloud Charts")
    except Exception:
        tracks = []
    if tracks:
        cache_set("charts", tracks, 1800)
    return tracks


def get_stream_url(target):
    cached = cache_get("u:" + target)
    if cached:
        return cached
    opts = {
        # Предпочитаем обычный http-файл (mp3), а не HLS: он лучше играет в браузере телефона
        "format": "bestaudio[protocol^=http][protocol!*=m3u8][protocol!*=dash]/bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
        "socket_timeout": 20,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(target, download=False)
        url = info.get("url")
    if url:
        cache_set("u:" + target, url, 1200)
    return url


@app.get("/stream")
def stream_query(url: str):
    try:
        direct = get_stream_url(url)
        if not direct:
            return {"error": "Не удалось получить аудиопоток"}
        return {"url": direct}
    except Exception as e:
        return {"error": str(e)}


@app.get("/stream/{video_id:path}")
def stream(video_id: str):
    return stream_query(video_id)
