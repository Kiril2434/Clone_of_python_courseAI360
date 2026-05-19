import aiohttp
from aiohttp import web
from yarl import URL


async def proxy_handler(request: web.Request) -> web.Response:
    """
    Check request contains http url in query args:
        /fetch?url=http%3A%2F%2Fexample.com%2F
    and trying to fetch it and return body with http status.
    If url passed without scheme or is invalid raise 400 Bad request.
    On failure raise 502 Bad gateway.
    :param request: aiohttp.web.Request to handle
    :return: aiohttp.web.Response
    """
    if request.path != "/fetch":
        raise web.HTTPBadGateway
    try:
        url = URL(request.query["url"])
    except KeyError:
        raise web.HTTPBadRequest(text="No url to fetch")
    if url.scheme != "http":
        if url.scheme == "":
            raise web.HTTPBadRequest(text="Empty url scheme")
        raise web.HTTPBadRequest(text=f"Bad url scheme: {url.scheme}")
    try:
        res = await request["session"].get(url)
    except KeyError:
        res = await aiohttp.ClientSession().get(url)
    if res.status == 200:
        raise web.HTTPOk(body=await res.read())
    raise web.HTTPInternalServerError(body=await res.read())



async def setup_application(app: web.Application) -> None:
    """
    Setup application routes and aiohttp session for fetching
    :param app: app to apply settings with
    """
    app.add_routes([web.get("/fetch", proxy_handler)])
    app["session"] = aiohttp.ClientSession()


async def teardown_application(app: web.Application) -> None:
    """
    Application with aiohttp session for tearing down
    :param app: app for tearing down
    """
    session = app["session"]
    await session.close()
