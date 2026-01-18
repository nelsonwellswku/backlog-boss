from contextlib import asynccontextmanager
from typing import Annotated, TypeAlias

import httpx
from fastapi import Depends, FastAPI, Request


@asynccontextmanager
async def configure_httpx_lifespan(app: FastAPI):
    with httpx.Client() as client:
        app.state.http_client = client
        yield


def get_http_client(request: Request):
    return request.app.state.http_client


HttpClient: TypeAlias = Annotated[httpx.Client, Depends(get_http_client)]
