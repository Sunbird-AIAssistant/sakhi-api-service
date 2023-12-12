from logger import logger
from translator import *
import time



def process_incoming_voice(file_url, input_language):
    error_message = None
    try:
        regional_text = audio_input_to_text(file_url, input_language)
        try:
            english_text = indic_translation(text=regional_text, source=input_language, destination='en')
        except Exception as e:
            error_message = "Indic translation to English failed"
            logger.error(f"Exception occurred: {e}", exc_info=True)
            english_text = None
    except Exception as e:
        error_message = "Speech to text conversion API failed"
        logger.error(f"Exception occurred: {e}", exc_info=True)
        regional_text = None
        english_text = None
    return regional_text, english_text, error_message


def process_incoming_text(regional_text, input_language):
    error_message = None
    try:
        english_text = indic_translation(text=regional_text, source=input_language, destination='en')
    except Exception as e:
        error_message = "Indic translation to English failed"
        english_text = None
        logger.error(f"Exception occurred: {e}", exc_info=True)
    return english_text, error_message


def process_outgoing_text(english_text, input_language):
    error_message = None
    try:
        regional_text = indic_translation(text=english_text, source='en', destination=input_language)
    except Exception as e:
        error_message = "English translation to indic language failed"
        logger.error(f"Exception occurred: {e}", exc_info=True)
        regional_text = None
    return regional_text, error_message


def process_outgoing_voice(message, input_language):
    error_message = None
    decoded_audio_content = text_to_speech(language=input_language, text=message)
    if decoded_audio_content is not None:
        logger.info("Creating output MP3 file")
        time_stamp = time.strftime("%Y%m%d-%H%M%S")
        filename = "audio-output-" + time_stamp + ".mp3"
        output_mp3_file = open(filename, "wb")
        output_mp3_file.write(decoded_audio_content)
        logger.info("Audio Response is saved as a MP3 file.")
        return output_mp3_file, error_message
    error_message = "Text to Audio conversion failed"
    logger.error(error_message)
    return None, error_message
