from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import yt_dlp
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

yt = YTMusic()

def get_thumbnail(entry):
    """Безопасное извлечение обложки с запасным вариантом (плейсхолдером)"""
    thumb = entry.get("thumbnail")
    if not thumb and entry.get("thumbnails"):
        thumbs = entry.get("thumbnails")
        if isinstance(thumbs, list) and len(thumbs) > 0:
            thumb = thumbs[-1].get("url")
    if not thumb:
        # Стильная заглушка, если обложка у трека отсутствует
        thumb = "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&auto=format&fit=crop&q=80"
    return [{"url": thumb}]

@app.get("/")
def root():
    return {"status": "Backend is running!"}

@app.get("/search")
def search(q: str):
    results = []

    # 1. YouTube Music
    try:
        yt_results = yt.search(q, filter="songs")
        for item in yt_results[:5]:
            results.append({
                "videoId": item.get("videoId"),
                "title": item.get("title"),
                "artists": item.get("artists", []),
                "thumbnails": item.get("thumbnails", [ {"url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&auto=format&fit=crop&q=80"} ]),
                "source": "YouTube"
            })
    except Exception:
        pass

    # 2. Spotify
    try:
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            sp_info = ydl.extract_info(f"spsearch4:{q}", download=False)
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

    # 3. Apple Music
    try:
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            am_info = ydl.extract_info(f"amsearch4:{q}", download=False)
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

    # 4. SoundCloud
    try:
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            sc_info = ydl.extract_info(f"scsearch4:{q}", download=False)
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

    return results[:20]

@app.get("/stream/{video_id:path}")
def stream(video_id: str):
    # Если это прямая ссылка (Spotify, Apple Music, SoundCloud)
    if video_id.startswith("http"):
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_id, download=False)
                url = info.get('url')
            if url:
                return {"url": url}
        except Exception as e:
            return {"error": str(e)}

    # Получение потока с YouTube через Cobalt API
    yt_url = f"https://www.youtube.com/watch?v={video_id}"
    payload = {
        "url": yt_url,
        "isAudioOnly": True
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "url" in data:
                return {"url": data["url"]}
            elif "picker" in data and len(data["picker"]) > 0:
                return {"url": data["picker"][0]["url"]}
    except Exception as e:
        print("Cobalt error:", e)

    return {"error": "Не удалось получить аудиопоток с YouTube"}
    
