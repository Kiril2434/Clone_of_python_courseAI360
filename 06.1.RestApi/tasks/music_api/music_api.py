from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
import secrets

app = FastAPI()
user_db = {}
track_db = {}
track_cnt = 0

class User(BaseModel):
    name: str
    age: int

@app.post("/api/v1/registration/register_user", status_code=201)
def add_user(user: User):
    user_token = str(secrets.token_hex(20))
    user_db[user_token] = user
    return {"token": user_token}

def check_token(x_token: str | None = Header(None)):
    if x_token is None:
        raise HTTPException(status_code=401, detail="Missing token")
    elif x_token not in user_db:
        raise HTTPException(status_code=401, detail="Incorrect token")

class Track(BaseModel):
    name: str
    artist: str
    year: int | None = None
    genres: list[str] | None = None

@app.post("/api/v1/tracks/add_track", status_code=201)
def add_track(track: Track, x_token: str | None = Depends(check_token)):
    global track_cnt
    track_cnt += 1
    track_db[track_cnt] = {
        "name": track.name,
        "artist": track.artist,
        "year": track.year,
        "genres": track.genres or []
    }
    return {"track_id": track_cnt}

@app.delete("/api/v1/tracks/{track_id}", status_code=200)
def delete_track(track_id: int, x_token: str | None = Depends(check_token)):
    if track_id not in track_db:
        raise HTTPException(status_code=404, detail="Invalid track_id")
    del track_db[track_id]
    return {"status": "track removed"}

@app.get("/api/v1/tracks/all", status_code=200)
def get_track_all(x_token: str | None = Depends(check_token)):
    return list(track_db.values())

@app.get("/api/v1/tracks/search", status_code=200)
def search_track(name: str | None = None, artist: str | None = None, x_token: str | None = Depends(check_token)):
    if name is None and artist is None:
        raise HTTPException(status_code=422, detail="You should specify at least one search argument")
    res = list(track_db.keys())
    if name is not None:
        res = [track_id for track_id in res if track_db[track_id]['name'] == name]
    if artist is not None:
        res = [track_id for track_id in res if track_db[track_id]['artist'] == artist]
    return {"track_ids": res}

@app.get("/api/v1/tracks/{track_id}", status_code=200)
def get_track(track_id: int, x_token: str | None = Depends(check_token)):
    if track_id not in track_db:
        raise HTTPException(status_code=404, detail="Invalid track_id")
    track = track_db[track_id]
    return {"name": track['name'], "artist": track['artist']}
