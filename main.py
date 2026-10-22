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

yt = YTMusic()  # Базовый поиск без авторизации[span_1](start_span)[span_1](end_span)

@app.get("/")
def root():
    return {"status": "Backend is running!"}

@app.get("/search")
def search(q: str):
    results = yt.search(q, filter="songs")
    return results[:15]

@app.get("/stream/{video_id}")
def stream(video_id: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://music.youtube.com/watch?v={video_id}", download=False)
        url = info.get('url')
    return {"url": url}
    
