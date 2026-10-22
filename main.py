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
                "thumbnails": item.get("thumbnails", []),
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
                            "thumbnails": [{"url": entry.get("thumbnail") or ""}],
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
                            "thumbnails": [{"url": entry.get("thumbnail") or ""}],
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
                            "thumbnails": [{"url": entry.get("thumbnail") or ""}],
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

    # Если это трек с YouTube — получаем поток через публичные защищенные шлюзы (обход капчи)
    piped_instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.tokhmi.xyz",
        "https://pipedapi.privacy.com.de"
    ]
    
    for instance in piped_instances:
        try:
            res = requests.get(f"{instance}/streams/{video_id}", timeout=5)
            if res.status_code == 200:
                data = res.json()
                audio_streams = data.get("audioStreams", [])
                if audio_streams:
                    best_stream = max(audio_streams, key=lambda x: x.get("bitrate", 0))
                    return {"url": best_stream.get("url")}
        except Exception:
            continue

    return {"error": "Не удалось получить аудиопоток с YouTube"}
    
