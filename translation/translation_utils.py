import os
import requests
import base64
from pydub import AudioSegment
from utils import *


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





