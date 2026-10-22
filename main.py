from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import yt_dlp

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

    # 2. Spotify (через yt-dlp spsearch)
    try:
        ydl_opts = {'extract_flat': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            sp_info = ydl.extract_info(f"spsearch5:{q}", download=False)
            if sp_info and 'entries' in sp_info:
                for entry in sp_info['entries']:
                    if entry and entry.get('url'):
                        results.append({
                            "videoId": entry.get('url'),
                            "title": entry.get("title"),
                            "artists": [{"name": entry.get("uploader") or entry.get("artist") or "Spotify Artist"}],
                            "thumbnails": [{"url": entry.get("thumbnail") or ""}],
                            "source": "Spotify"
                        })
    except Exception:
        pass

    # 3. Apple Music (через yt-dlp amsearch)
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
                            "artists": [{"name": entry.get("uploader") or "Apple Music Artist"}],
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
                            "artists": [{"name": entry.get("uploader") or "SoundCloud Artist"}],
                            "thumbnails": [{"url": entry.get("thumbnail") or ""}],
                            "source": "SoundCloud"
                        })
    except Exception:
        pass

    return results[:20]

@app.get("/stream/{video_id:path}")
def stream(video_id: str):
    if video_id.startswith("http"):
        target = video_id
    else:
        target = f"https://music.youtube.com/watch?v={video_id}"

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
        
