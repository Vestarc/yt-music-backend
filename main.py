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
    return {"status": "Backend is running!"}

@app.get("/search")
def search(q: str):
    results = []

    # 1. Spotify (основной каталог)
    try:
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            sp_info = ydl.extract_info(f"spsearch20:{q}", download=False)
            if sp_info and 'entries' in sp_info:
                for entry in sp_info['entries']:
                    if entry and entry.get('url'):
                        results.append({
                            "videoId": entry.get('url'),
                            "title": entry.get("title"),
                            "artists": [{"name": entry.get("uploader") or entry.get("artist") or "Spotify"}],
                            "thumbnails": get_thumbnail(entry),
                            "source": "Spotify"
                        })
    except Exception:
        pass

    # 2. Apple Music
    try:
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            am_info = ydl.extract_info(f"amsearch15:{q}", download=False)
            if am_info and 'entries' in am_info:
                for entry in am_info['entries']:
                    if entry and entry.get('url'):
                        results.append({
                            "videoId": entry.get('url'),
                            "title": entry.get("title"),
                            "artists": [{"name": entry.get("uploader") or "Apple Music"}],
                            "thumbnails": get_thumbnail(entry),
                            "source": "Apple Music"
                        })
    except Exception:
        pass

    # 3. SoundCloud
    try:
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            sc_info = ydl.extract_info(f"scsearch15:{q}", download=False)
            if sc_info and 'entries' in sc_info:
                for entry in sc_info['entries']:
                    if entry and entry.get('url'):
                        results.append({
                            "videoId": entry.get('url'),
                            "title": entry.get("title"),
                            "artists": [{"name": entry.get("uploader") or "SoundCloud"}],
                            "thumbnails": get_thumbnail(entry),
                            "source": "SoundCloud"
                        })
    except Exception:
        pass

    return results

@app.get("/charts")
def charts():
    # Чарты на основе глобальных хитов Spotify
    try:
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info("spsearch25:global top hits", download=False)
            tracks = []
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry and entry.get('url'):
                        tracks.append({
                            "videoId": entry.get('url'),
                            "title": entry.get("title"),
                            "artists": [{"name": entry.get("uploader") or entry.get("artist") or "Spotify"}],
                            "thumbnails": get_thumbnail(entry),
                            "source": "Spotify"
                        })
            if tracks:
                return tracks
    except Exception:
        pass
    
    # Запасной вариант через SoundCloud
    try:
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info("scsearch20:pop hits", download=False)
            tracks = []
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry and entry.get('url'):
                        tracks.append({
                            "videoId": entry.get('url'),
                            "title": entry.get("title"),
                            "artists": [{"name": entry.get("uploader") or "SoundCloud"}],
                            "thumbnails": get_thumbnail(entry),
                            "source": "SoundCloud"
                        })
            if tracks:
                return tracks
    except Exception:
        pass

    return []

@app.get("/stream/{video_id:path}")
def stream(video_id: str):
    # Прямая загрузка потока для треков со Spotify, Apple Music, SoundCloud
    target = video_id if video_id.startswith("http") else f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
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
                                                           
