from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from demo_8_tests import posts

app = FastAPI(debug=True)
app.include_router(posts.router, prefix="/posts", tags=["posts"])

@app.exception_handler(IndexError)
def index_error_handler(request: Request, exc: IndexError):
    # return JSONResponse(
    #   status_code=404,
    #   content={"message": "No such element"}
    # )
    # pyrefly: ignore  # unknown-name
    return PlainTextResponse("No such element", status_code=404)


@app.get("/")
def get_index():
    return "Hello!"
