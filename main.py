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

    # 1. YouTube Music (полная выдача)
    try:
        yt_results = yt.search(q, filter="songs")
        for item in yt_results:
            results.append({
                "videoId": item.get("videoId"),
                "title": item.get("title"),
                "artists": item.get("artists", []),
                "thumbnails": item.get("thumbnails", [{"url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&auto=format&fit=crop&q=80"}]),
                "source": "YouTube"
            })
    except Exception:
        pass

    # 2. Spotify, Apple Music, SoundCloud
    for service, prefix in [("Spotify", "spsearch15"), ("Apple Music", "amsearch15"), ("SoundCloud", "scsearch15")]:
        try:
            ydl_opts = {'extract_flat': True, 'quiet': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"{prefix}:{q}", download=False)
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry and entry.get('url'):
                            results.append({
                                "videoId": entry.get('url'),
                                "title": entry.get("title"),
                                "artists": [{"name": entry.get("uploader") or entry.get("artist") or service, "id": None}],
                                "thumbnails": get_thumbnail(entry),
                                "source": service
                            })
        except Exception:
            pass

    return results

@app.get("/charts")
def charts():
    try:
        chart_data = yt.get_charts(country="RU")
        tracks = []
        items = chart_data.get("videos", {}).get("items", []) or chart_data.get("songs", {}).get("items", [])
        for item in items:
            tracks.append({
                "videoId": item.get("videoId"),
                "title": item.get("title"),
                "artists": item.get("artists", []),
                "thumbnails": item.get("thumbnails", []),
                "source": "YouTube"
            })
        if not tracks:
            return search("Top hits 2026")
        return tracks
    except Exception:
        return search("Top hits")

@app.get("/artist/{channel_id}")
def artist_info(channel_id: str):
    try:
        data = yt.get_artist(channel_id)
        tracks = []
        for item in data.get("songs", {}).get("results", []):
            tracks.append({
                "videoId": item.get("videoId"),
                "title": item.get("title"),
                "artists": item.get("artists", [{"name": data.get("name")}]),
                "thumbnails": item.get("thumbnails", []),
                "source": "YouTube"
            })
        return {
            "name": data.get("name"), 
            "thumbnails": data.get("thumbnails", [{"url": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=150&auto=format&fit=crop&q=80"}]), 
            "tracks": tracks
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/stream/{video_id:path}")
def stream(video_id: str):
    if video_id.startswith("http"):
        target = video_id
    else:
        target = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android']
            }
        }
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
            
