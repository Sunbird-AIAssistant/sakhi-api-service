from translation.BaseTranslationClass import BaseTranslationClass
from translation.translation_utils import *
import requests
from translation.telemetry import *
import json
import base64
import time
from config_util import get_config_value


class DhruvaTranslationClass(BaseTranslationClass):

    def __init__(self) -> None:
        self.asr_mapping = {
            "bn": "ai4bharat/conformer-multilingual-indo-aryan--gpu-t4",
            "en": "ai4bharat/whisper--gpu-t4",
            "gu": "ai4bharat/conformer-multilingual-indo-aryan--gpu-t4",
            "hi": "ai4bharat/conformer-hi--gpu-t4",
            "kn": "ai4bharat/conformer-multilingual-dravidian--gpu-t4",
            "ml": "ai4bharat/conformer-multilingual-dravidian--gpu-t4",
            "mr": "ai4bharat/conformer-multilingual-indo-aryan--gpu-t4",
            "or": "ai4bharat/conformer-multilingual-indo-aryan--gpu-t4",
            "pa": "ai4bharat/conformer-multilingual-indo-aryan--gpu-t4",
            "sa": "ai4bharat/conformer-multilingual-indo-aryan--gpu-t4",
            "ta": "ai4bharat/conformer-multilingual-dravidian--gpu-t4",
            "te": "ai4bharat/conformer-multilingual-dravidian--gpu-t4",
            "ur": "ai4bharat/conformer-multilingual-indo-aryan--gpu-t4"

        }

        self.translation_serviceId = "ai4bharat/indictrans--gpu-t4"

        self.tts_mapping = {
            "as": "ai4bharat/indic-tts-indo-aryan--gpu-t4",
            "bn": "ai4bharat/indic-tts-indo-aryan--gpu-t4",
            "brx": "ai4bharat/indic-tts-misc--gpu-t4",
            "en": "ai4bharat/indic-tts-misc--gpu-t4",
            "gu": "ai4bharat/indic-tts-indo-aryan--gpu-t4",
            "hi": "ai4bharat/indic-tts-indo-aryan--gpu-t4",
            "kn": "ai4bharat/indic-tts-dravidian--gpu-t4",
            "ml": "ai4bharat/indic-tts-dravidian--gpu-t4",
            "mni": "ai4bharat/indic-tts-misc--gpu-t4",
            "mr": "ai4bharat/indic-tts-indo-aryan--gpu-t4",
            "or": "ai4bharat/indic-tts-indo-aryan--gpu-t4",
            "pa": "ai4bharat/indic-tts-indo-aryan--gpu-t4",
            "raj": "ai4bharat/indic-tts-indo-aryan--gpu-t4",
            "ta": "ai4bharat/indic-tts-dravidian--gpu-t4",
            "te": "ai4bharat/indic-tts-dravidian--gpu-t4"

        }

    def translate_text(self, text, source, destination):
        if source == destination:
            return text
        try:
            start_time = time.time()
            url = get_config_value('translator', 'BHASHINI_ENDPOINT_URL', None)
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": source,
                                "targetLanguage": destination
                            },
                            "serviceId": self.translation_serviceId
                        }
                    }
                ],
                "inputData": {
                    "input": [
                        {
                            "source": text
                        }
                    ]
                }
            }
            headers = {
                'Authorization': get_config_value('translator', 'BHASHINI_API_KEY', None),
                'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            process_time = time.time() - start_time
            response.raise_for_status()
            log_success_telemetry_event(url, "POST", {"taskType": "translation"}, process_time, status_code=response.status_code)
            indic_text = json.loads(response.text)["pipelineResponse"][0]["output"][0]["target"]
        except requests.exceptions.RequestException as e:
            process_time = time.time() - start_time
            log_failed_telemetry_event(url, "POST", {"taskType": "translation"}, process_time, status_code=e.response.status_code, error=e.response.text)
            raise RequestError(e.response) from e
        return indic_text

    def speech_to_text(self, audio_file, input_language):
        encoded_string, wav_file_content = get_encoded_string(audio_file)
        start_time = time.time()
        url = get_config_value('translator', 'BHASHINI_ENDPOINT_URL', None)
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": {
                        "language": {
                            "sourceLanguage": input_language
                        },
                        "serviceId": self.asr_mapping[input_language]
                    }
                }
            ],
            "inputData": {
                "audio": [
                    {
                        "audioContent": encoded_string
                    }
                ]
            }
        }
        headers = {
            'Authorization': get_config_value('translator', 'BHASHINI_API_KEY', None),
            'Content-Type': 'application/json'
        }

        try:
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            process_time = time.time() - start_time
            response.raise_for_status()
            log_success_telemetry_event(url, "POST", {"taskType": "asr"}, process_time, status_code=response.status_code)
            text = json.loads(response.text)[
                "pipelineResponse"][0]["output"][0]["source"]
            return text
        except requests.exceptions.RequestException as e:
            process_time = time.time() - start_time
            log_failed_telemetry_event(url, "POST", {"taskType": "asr"}, process_time, status_code=e.response.status_code, error=e.response.text)
            raise RequestError(e.response) from e

    def text_to_speech(self, language, text, gender='female'):
        try:
            start_time = time.time()
            url = get_config_value('translator', 'BHASHINI_ENDPOINT_URL', None)
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {
                            "language": {
                                "sourceLanguage": language
                            },
                            "serviceId": self.tts_mapping[language],
                            "gender": gender
                        }
                    }
                ],
                "inputData": {
                    "input": [
                        {
                            "source": text
                        }
                    ],
                    "audio": [
                        {
                            "audioContent": None
                        }
                    ]
                }
            }
            headers = {
                'Authorization': get_config_value('translator', 'BHASHINI_API_KEY', None),
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            process_time = time.time() - start_time
            response.raise_for_status()
            log_success_telemetry_event(url, "POST", {"taskType": "tts"}, process_time, status_code=response.status_code)
            audio_content = response.json()["pipelineResponse"][0]['audio'][0]['audioContent']
            audio_content = base64.b64decode(audio_content)
        except requests.exceptions.RequestException as e:
            process_time = time.time() - start_time
            log_failed_telemetry_event(url, "POST", {"taskType": "tts"}, process_time, status_code=e.response.status_code, error=e.response.text)
            audio_content = None
            # audio_content = google_text_to_speech(text, language)
        return audio_content
