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

def get_thumbnail(entry):
    thumb = entry.get("thumbnail")
    if not thumb and entry.get("thumbnails"):
        thumbs = entry.get("thumbnails")
        if isinstance(thumbs, list) and len(thumbs) > 0:
            thumb = thumbs[-1].get("url")
    if not thumb:
        thumb = "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&auto=format&fit=crop&q=80"
    return [{"url": thumb}]

@app.get("/")
def root():
    return {"status": "YouMusic Core Engine Running"}

@app.get("/search")
def search(q: str):
    results = []
    seen_ids = set()

    # Надежные площадки без Яндекса: SoundCloud, Bandcamp и глобальная библиотека
    search_queries = [
        ("scsearch40:" + q, "SoundCloud"),
        ("bcsearch30:" + q, "Bandcamp"),
        ("ytsearch40:" + q + " audio", "Global Library")
    ]

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'extractor_args': {'youtube': {'player_client': ['android']}}
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for query, source_type in search_queries:
            try:
                info = ydl.extract_info(query, download=False)
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            # Для SoundCloud и Bandcamp берем строго полный URL, чтобы избежать ошибок с ID
                            vid = entry.get('url') if source_type in ["SoundCloud", "Bandcamp"] else (entry.get('id') or entry.get('url'))
                            if vid and str(vid) not in seen_ids:
                                seen_ids.add(str(vid))
                                results.append({
                                    "videoId": vid,
                                    "title": entry.get("title", "Unknown Title"),
                                    "artists": [{"name": entry.get("uploader") or entry.get("artist") or source_type}],
                                    "thumbnails": get_thumbnail(entry),
                                    "source": source_type
                                })
            except Exception:
                continue

    return results

@app.get("/charts")
def charts():
    tracks = []
    seen_ids = set()
    ydl_opts = {
        'extract_flat': True, 
        'quiet': True, 
        'ignoreerrors': True,
        'extractor_args': {'youtube': {'player_client': ['android']}}
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info("ytsearch40:global top hits audio", download=False)
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry and entry.get('url'):
                        vid = entry.get('id') or entry.get('url')
                        if vid and str(vid) not in seen_ids:
                            seen_ids.add(str(vid))
                            tracks.append({
                                "videoId": vid,
                                "title": entry.get("title", "Hit"),
                                "artists": [{"name": entry.get("uploader") or "Global Charts"}],
                                "thumbnails": get_thumbnail(entry),
                                "source": "Global Charts"
                            })
    except Exception:
        pass
    return tracks

@app.get("/stream/{video_id:path}")
def stream(video_id: str):
    # Если передан полноценный URL (SoundCloud, Bandcamp или прямая ссылка), используем его напрямую
    if video_id.startswith("http"):
        target = video_id
    else:
        target = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android']}}
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(target, download=False)
            url = info.get('url')
        
        if not url:
            return {"error": "Не удалось получить аудиопоток"}
        
        return {"url": url}
    except Exception as e:
        return {"error": str(e)}
            
