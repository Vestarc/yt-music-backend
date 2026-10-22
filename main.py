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

    # Мультипоточный поиск: SoundCloud и Яндекс Музыка
    search_targets = [
        f"scsearch50:{q}",
        f"https://music.yandex.ru/search?text={q}"
    ]

    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for target in search_targets:
            try:
                info = ydl.extract_info(target, download=False)
                if info:
                    entries = info.get('entries', [])
                    if not entries and 'url' in info:
                        entries = [info]

                    for entry in entries:
                        if entry and entry.get('url'):
                            vid = entry.get('id') or entry.get('url')
                            if vid not in seen_ids:
                                seen_ids.add(vid)
                                source_name = "Yandex Music" if "yandex.ru" in target else "SoundCloud"
                                results.append({
                                    "videoId": vid,
                                    "title": entry.get("title", "Unknown Title"),
                                    "artists": [{"name": entry.get("uploader") or entry.get("artist") or entry.get("creator") or source_name}],
                                    "thumbnails": get_thumbnail(entry),
                                    "source": source_name
                                })
            except Exception as e:
                continue

    return results

@app.get("/charts")
def charts():
    tracks = []
    seen_ids = set()
    ydl_opts = {'extract_flat': True, 'quiet': True, 'ignoreerrors': True}
    
    # Загрузка чартов из Яндекс Музыки
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info("https://music.yandex.ru/chart", download=False)
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry and entry.get('url'):
                        vid = entry.get('id') or entry.get('url')
                        if vid not in seen_ids:
                            seen_ids.add(vid)
                            tracks.append({
                                "videoId": vid,
                                "title": entry.get("title", "Hit"),
                                "artists": [{"name": entry.get("uploader") or entry.get("artist") or "Yandex Charts"}],
                                "thumbnails": get_thumbnail(entry),
                                "source": "Yandex Music"
                            })
    except Exception:
        pass

    # Резервный источник (SoundCloud), если чарты Яндекса не ответили
    if not tracks:
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info("scsearch40:global top hits", download=False)
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('url'):
                            vid = entry.get('id') or entry.get('url')
                            if vid not in seen_ids:
                                seen_ids.add(vid)
                                tracks.append({
                                    "videoId": vid,
                                    "title": entry.get("title", "Hit"),
                                    "artists": [{"name": entry.get("uploader") or "SoundCloud"}],
                                    "thumbnails": get_thumbnail(entry),
                                    "source": "SoundCloud"
                                })
        except Exception:
            pass

    return tracks

@app.get("/stream/{video_id:path}")
def stream(video_id: str):
    target = video_id if video_id.startswith("http") else f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'no_warnings': True,
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
        
