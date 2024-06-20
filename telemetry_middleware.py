import json
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import Message

from logger import logger
from telemetry_logger import TelemetryLogger
from utils import get_from_env_or_config, is_url 



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

def remove_base64_from_request(request):
    if not is_url(request["input"]["audio"]):
        request["input"]["audio"] = ""
        return request
    return request 

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
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        if "v1" in str(request.url):
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            response_body_json = json.loads(response_body.decode("utf-8"))
            event: dict = {
                "status_code": response.status_code,
                "duration": round(process_time * 1000),
                "body": response_body_json,
                "method": request.method,
                "url": request.url
            }
            # event.update(request.headers)
            logger.info({"label": "api_call", "event": event})

            if telemetry_log_enabled:
                if response.status_code == 200:
                    event = telemetryLogger.prepare_log_event(eventInput=event, message="success")
                else:
                    event["body"] = { **event["body"], **body}
                    event["body"] = remove_base64_from_request(event["body"])
                    event = telemetryLogger.prepare_log_event(eventInput=event, elevel="ERROR", message="failed")
                telemetryLogger.add_event(event)

            if "output" in response_body_json:
                response_body_str = json.dumps({"output": response_body_json["output"]}, indent=2)
            else:
                response_body_str = json.dumps(response_body_json, indent=2)
            modified_response = response_body_str.encode("utf-8")
            response.headers['Content-Length'] = str(len(modified_response))
            return Response(content=response_body_str, headers=dict(response.headers), status_code=response.status_code,media_type=response.media_type)
            
        return response
