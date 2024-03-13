import os
import requests
import json
import base64
import time
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate
from pydub import AudioSegment

from logger import logger
from config_util import get_config_value
from utils import *
from translation.telemetry import *

def get_encoded_string(audio):
    if is_url(audio):
        local_filename = generate_temp_filename("mp3")
        with requests.get(audio) as r:
            with open(local_filename, 'wb') as f:
                f.write(r.content)
    elif is_base64(audio):
        local_filename = generate_temp_filename("mp3")
        decoded_audio_content = base64.b64decode(audio)
        output_mp3_file = open(local_filename, "wb")
        output_mp3_file.write(decoded_audio_content)
        output_mp3_file.close()
    else:
        local_filename = audio

    output_file = AudioSegment.from_file(local_filename)
    mp3_output_file = output_file.export(local_filename, format="mp3")
    given_audio = AudioSegment.from_file(mp3_output_file)
    given_audio = given_audio.set_frame_rate(16000)
    given_audio = given_audio.set_channels(1)
    tmp_wav_filename = generate_temp_filename("wav")
    given_audio.export(tmp_wav_filename, format="wav", codec="pcm_s16le")
    with open(tmp_wav_filename, "rb") as wav_file:
        wav_file_content = wav_file.read()
    encoded_string = base64.b64encode(wav_file_content)
    encoded_string = str(encoded_string, 'ascii', 'ignore')
    os.remove(local_filename)
    os.remove(tmp_wav_filename)
    return encoded_string, wav_file_content


class RequestError(Exception):
    def __init__(self, response):
        self.response = response


class TranslationClass:
    def __init__(self):
        pass

    def translate_text(self, text):
        pass

    def translate_file(self, file_path):
        pass

    def text_to_speech(self, language, text):
        pass

    def speech_to_text(self, audio_file, input_language):
        pass
    
    def detect_language(self):
        pass

    



class BhashiniTranslationClass(TranslationClass):
    
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


class GoogleCloudTranslationClass(TranslationClass):
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GCP_CONFIG_PATH")

    

    def translate_text(self, text, source, destination):
        client = translate.Client()
        try:
            result = client.translate(text, target_language=destination)
        except Exception as error:
            #log telemetry event
            logger.info(f"error during google translation")
        return result['translatedText']

    def speech_to_text(self, audio_file, input_language):
        encoded_string, wav_file_content = get_encoded_string(audio_file)
        client = speech.SpeechClient()


        audio = speech.RecognitionAudio(content=encoded_string)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        response = client.recognize(config=config, audio=audio)
        # log telemetry
        if response.results:
            return response.results[0].alternatives[0].transcript
        else:
            # log failed telemetry
            return "No speech detected."

    def text_to_speech(self, language, text):
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Use a female voice
        voice = texttospeech.VoiceSelectionParams(
            language_code=language, ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return response.audio_content
