import time
import json
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from telemetry_logger import TelemetryLogger
from starlette.types import Message

class TelemetryMiddleware(BaseHTTPMiddleware):
    def __init__(
            self,
            app
    ):
        super().__init__(app)

    # https://github.com/tiangolo/fastapi/issues/394 
    # Stream response does not work => https://github.com/tiangolo/fastapi/issues/394#issuecomment-994665859   
    async def set_body(self, request: Request):
        receive_ = await request._receive()
        async def receive() -> Message:
            return receive_
        request._receive = receive

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        await self.set_body(request)
        body = await request.body()
        if body.decode("utf-8"):
            body = json.loads(body)
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        if "v1" in str(request.url):
            telemetryLogger =  TelemetryLogger()
            event: dict = {
                "status_code": response.status_code,
                "duration": round(process_time * 1000),
                "body": body,
                "method": request.method,
                "url": request.url
            }
            event.update(request.headers)
            if response.status_code == 200:
                event = telemetryLogger.prepare_log_event(eventInput=event, message="success")
            else:
                event = telemetryLogger.prepare_log_event(eventInput=event, elevel="ERROR", message="failed")
            telemetryLogger.add_event(event)
        return response