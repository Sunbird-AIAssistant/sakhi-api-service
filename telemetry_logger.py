import requests
import time
import os
import uuid
from logger import logger

telemetryURL = os.environ.get("TELEMETRY_ENDPOINT_URL", "")
ENV_NAME = os.environ.get("SERVICE_ENVIRONMENT", "dev")
TELEMETRY_LOG_ENABLED = os.environ.get("TELEMETRY_LOG_ENABLED", "true").lower() == "true"


class TelemetryLogger:
    """
    A class to capture and send telemetry logs using the requests library with threshold limit.
    """

    def __init__(self, url=telemetryURL, threshold=5):
        self.url = url
        self.events = []  # Store multiple events before exceeding threshold
        self.threshold = threshold

    def add_event(self, event):
        """
        Adds a telemetry event to the log.

        **kwargs:** Keyword arguments containing the event data.
        """

        logger.info(f"Telemetry event: {event}")

        if not TELEMETRY_LOG_ENABLED:
            return

        self.events.append(event)
        # Send logs if exceeding threshold
        if len(self.events) >= self.threshold:
            self.send_logs()

    def send_logs(self):
        """
        Sends the captured telemetry logs using the requests library.
        """
        try:
            data = {
                "id": "api.djp.telemetry",
                "ver": "3.1",
                "params": {"msgid": str(uuid.uuid4())},
                "ets": int(time.time() * 1000),
                "events": self.events
            }
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.url + "/v1/telemetry", json=data, headers=headers)
            response.raise_for_status()
            logger.debug(f"Telemetry API request data: {data}")
            logger.info("Telemetry logs sent successfully!")
            # Reset captured events after sending
            self.events = []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending telemetry log: {e}", exc_info=True)

    def prepare_log_event(self, eventInput: dict, etype="api_access", elevel="INFO", message=""):
        """
        Prepare a telemetry event dictionary with the specified values.
        Args:
            eventInput: Event Input.
            etype: Event type (default: "api_access").
            elevel: Event level (default: "INFO").
            message: Event message.

        Returns:
            A dictionary representing the telemetry event data.
        """
        data = {
            "eid": "LOG",
            "ets": int(time.time() * 1000),  # Current timestamp
            "ver": "3.1",  # Version
            "mid": f"LOG:{round(time.time())}",  # Unique message ID
            "actor": {
                "id": "sakhi-api-service",
                "type": "System",
            },
            "context": {
                "channel": "ejp",
                "pdata": {
                    "id": "ejp.sakhi.api.service",
                    "ver": "1.0",
                    "pid": ""
                },
                "env": ENV_NAME
            },
            "edata": {
                "type": etype,
                "level": elevel,
                "message": str(message).replace("'", "")
            }
        }

        if eventInput.get("x-request-id", None):
            data["context"]["sid"] = eventInput.get("x-request-id")

        if eventInput.get("x-device-id", None):
            data["context"]["did"] = eventInput.get("x-device-id")

        eventCData = self.__getEventCData(eventInput)
        if eventCData:
            data["context"]["cdata"] = eventCData

        eventEDataParams = self.__getEventEDataParams(eventInput)
        if eventEDataParams:
            data["edata"]["params"] = eventEDataParams
        return data

    def __getEventCData(self, eventInput: dict):
        eventCData = []
        if eventInput.get("x-consumer-id", None) and eventInput.get("x-source", None):
            eventCData = [
                {
                    "id": eventInput.get("x-consumer-id"),
                    "type": "ConsumerId"
                },
                {
                    "id": eventInput.get("x-source"),
                    "type": "Source"
                }
            ]
        return eventCData

    def __getEventEDataParams(self, eventInput: dict):
        eventEDataParams = [
            {"method": str(eventInput.get("method"))},
            {"url": str(eventInput.get("url"))},
            {"status": eventInput.get("status_code")},
            {"duration": int(eventInput.get("duration"))}
        ]
        flattened_dict = self.__flatten_dict(eventInput.get("body", {}))
        if bool(flattened_dict):
            for item in flattened_dict.items():
                eventEDataParams.append({item[0]: item[1]})

        return eventEDataParams

    def __flatten_dict(self, d, parent_key='', sep='_'):
        flattened = {}
        if bool(d):
            for k, v in d.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, dict):
                    flattened.update(self.__flatten_dict(v, new_key, sep=sep))
                else:
                    flattened[new_key] = v

        return flattened
