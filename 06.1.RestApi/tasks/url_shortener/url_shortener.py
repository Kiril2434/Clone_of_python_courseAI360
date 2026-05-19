import typing as tp
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel


app = FastAPI()

db: dict[str, str] = {}


class ToShort(BaseModel):
    url: str


class Shorted(BaseModel):
    url: str
    key: str


@app.post("/shorten", status_code=201, summary="Short Url")
def short_url(url: ToShort) -> Shorted:
    for existing_key, existing_url in db.items():
        if existing_url == url.url:
            return Shorted(url=url.url, key=existing_key)
    key = str(uuid.uuid4())
    db[key] = url.url
    return Shorted(url=url.url, key=key)


@app.get("/go/{key}", status_code=307, response_model=tp.Any)
def redirect_to_url(key: str):
    if key not in db:
        raise HTTPException(status_code=404)
    return RedirectResponse(url=db[key])
