from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yt = YTMusic()

@app.get("/api/search")
def search_tracks(q: str):
    try:
        results = yt.search(q, filter="songs")
        tracks = []
        for item in results[:10]:
            tracks.append({
                "id": item.get("videoId"),
                "title": item.get("title"),
                "artist": item.get("artists", [{}])[0].get("name", "Неизвестный исполнитель"),
                "cover": item.get("thumbnails", [{}])[-1].get("url"),
            })
        return {"tracks": tracks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stream")
def get_stream_url(video_id: str):
    ydl_opts = {'format': 'bestaudio/best', 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return {"audio_url": info['url']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        