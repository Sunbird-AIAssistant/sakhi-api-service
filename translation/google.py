from logger import logger
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import texttospeech
from google.cloud import translate_v2 as translate

from translation.base import BaseTranslationClass
from translation.translation_utils import *


class GoogleCloudTranslationClass(BaseTranslationClass):
    def __init__(self):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GCP_CONFIG_PATH")

    def translate_text(self, text: str, source: str, destination: str):
        client = translate.Client()
        try:
            result = client.translate(text, target_language=destination)
        except Exception as error:
            # log telemetry event
            logger.info(f"error during google translation")
        return result['translatedText']

    def speech_to_text(self, audio_file: Any, input_language: str):
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

    def text_to_speech(self, language: str, text: str, gender=texttospeech.SsmlVoiceGender.FEMALE):
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Use a female voice
        voice = texttospeech.VoiceSelectionParams(
            language_code=language, ssml_gender=gender
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        return response.audio_content
