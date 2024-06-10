import json
import re
import time

from fastapi import Request
from pydantic import constr
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import Message

from logger import logger
from telemetry_logger import TelemetryLogger
from utils import get_from_env_or_config


# https://github.com/tiangolo/fastapi/issues/394
# Stream response does not work => https://github.com/tiangolo/fastapi/issues/394#issuecomment-994665859
async def set_body(request: Request, body: bytes):
    async def receive() -> Message:
        return {"type": "http.request", "body": body}

    request._receive = receive


async def get_body(request: Request) -> bytes:
    body = await request.body()
    await set_body(request, body)
    return body


telemetryLogger = TelemetryLogger()
telemetry_log_enabled = get_from_env_or_config('telemetry', 'telemetry_log_enabled', None).lower() == "true"


routes_with_middleware = ["/"]
rx = re.compile(r'^(/v1/[a-zA-Z0-9]+)$')  # support routes with path parameters
my_constr = constr(regex="^[a-zA-Z0-9]+$")


class TelemetryMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app
    ):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        await set_body(request, await request.body())
        body = await get_body(request)
        if body.decode("utf-8"):
            body = json.loads(body)
        response = await call_next(request)
        if request.url.path not in routes_with_middleware and not rx.match(request.url.path):
            return response
        else:
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            if "v1" in str(request.url):
                event: dict = {
                    "status_code": response.status_code,
                    "duration": round(process_time * 1000),
                    "body": response_body.decode(),
                    "method": request.method,
                    "url": request.url
                }
                # event.update(request.headers)
                logger.info({"label": "api_call", "event": event})

                if telemetry_log_enabled:
                    if response.status_code == 200:
                        event = telemetryLogger.prepare_log_event(eventInput=event, message="success")
                    else:
                        event = telemetryLogger.prepare_log_event(eventInput=event, elevel="ERROR", message="failed")
                    telemetryLogger.add_event(event)

            if "output" in json.loads(response_body.decode()):
                response_body_json = json.dumps({"output": json.loads(response_body.decode())["output"]}, indent=2)
            else:
                response_body_json = json.dumps(json.loads(response_body.decode()), indent=2)

            json_response = Response(content=response_body_json, status_code=response.status_code, media_type="application/json")
            return json_response
