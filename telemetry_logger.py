from fastapi.datastructures import Headers
import requests
import time
import os
import uuid
from logger import logger

telemetryURL = os.environ["TELEMETRY_ENDPOINT_URL"]

class TelemetryLogger:
    """
    A class to capture and send telemetry logs using the requests library with threshold limit.
    """

    def __init__(self, url=telemetryURL, threshold=1):
        self.url = url
        self.events = []  # Store multiple events before exceeding threshold
        self.threshold = threshold

    def add_event(self, event):
        """
        Adds a telemetry event to the log.

        **kwargs:** Keyword arguments containing the event data.
        """
        # Check for required fields
        # if not ("eid" in event or "object" in event):
        #     raise ValueError("Missing required field(s) for event: 'eid' or 'object'")
        logger.info(f"event: {event}")
        self.events.append(event)

        # Send logs if exceeding threshold
        if len(self.events) >= self.threshold:
            self.send_logs()

    def send_logs(self):
        """
        Sends the captured telemetry logs using the requests library.
        """
        data = {
            "id": "api.djp.telemetry",
            "ver": "1.0",
            "params": {"msgid": str(uuid.uuid4())},
            "ets": int(time.time() * 1000),
            "events": self.events,
        }
        headers = {"Content-Type": "application/json"}
        response = requests.post(self.url + "/v1/telemetry", json=data, headers=headers)
        logger.debug(f"Telemetry API request data: {data}")
        if response.status_code != 200:
            logger.error(f"Error sending telemetry log: {response.status_code} - {response.text}")
        else:
            logger.info("Telemetry logs sent successfully!")

        # Reset captured events after sending
        self.events = []

    def prepare_log_event(self, headers: dict, body, etype = "api_access", elevel = "INFO", message=""):
        """
        Prepare a telemetry event dictionary with the specified values. 
        Args:
            eid: Event identifier (e.g., "LOG").
            message: Event message.
            user_id: User ID.
            channel: Event channel (default: "01269878797503692810").
            level: Event level (default: "ERROR").
            pageid: Page ID where the event occurred (default: "/").

        Returns:
            A dictionary representing the telemetry event data.
        """

        data = {
            "eid": "LOG",
            "ets": int(time.time() * 1000),  # Current timestamp
            "ver": "1.0",  # Version
            "mid": f"LOG:{round(time.time())}",  # Unique message ID
            "actor": {
                "id": "sakhi-api-service",
                "type": "System",
            },
            "context": {
                "channel": "sakhi-api-service",
                 "pdata": {
                    "id": "djp.sakhi.api.service",
                    "ver": "1.0.0",
                    "pid": ""
                },
                "env": "sakhi-api-service",
                "sid":headers.get("x-request-id", ""), # Optional. session id of the requestor stamped by portal
                "did": headers.get("x-device-id", ""), # Optional. uuid of the device, created during app installation
                "cdata": [
                    {
                        "id": headers.get("x-consumer-id", ""),
                        "type": "UserSession"
                    },
                    {
                        "id": headers.get("X-Source", ""),
                        "type": "Device"
                    }
                ]
            },
            "object": {},  # Can be populated with relevant event data if needed
            "tags": [],  # Add relevant tags if any
            "edata": {
                "type": etype,  # Required. Type of log (system, process, api_access, api_call, job, app_update etc)
                "level": elevel, # Required. Level of the log. TRACE, DEBUG, INFO, WARN, ERROR, FATAL
                "message": message, # Required. Log message
                "params": [body], # Optional. Additional params in the log message
            }
        }
        return data