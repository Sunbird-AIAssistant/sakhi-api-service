from telemetry_logger import TelemetryLogger
from env_manager import translate_class as translator

telemetryLogger = TelemetryLogger()

def log_success_telemetry_event(url, method, payload, process_time, status_code):
    event: dict = {
        "status_code": status_code,
        "duration": round(process_time * 1000),
        "body": payload,
        "method": method,
        "url": url
    }
    event = telemetryLogger.prepare_log_event(eventInput=event, etype="api_call", elevel="INFO", message="success")
    telemetryLogger.add_event(event)


def log_failed_telemetry_event(url, method, payload, process_time, status_code, error):
    event: dict = {
        "status_code": status_code,
        "duration": round(process_time * 1000),
        "body": payload,
        "method": method,
        "url": url
    }
    error = error.replace("'", "")
    event = telemetryLogger.prepare_log_event(eventInput=event, etype="api_call", elevel="ERROR", message=error)
    telemetryLogger.add_event(event)

