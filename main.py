import os.path
from enum import Enum
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from io_processing import *
from query_with_langchain import *
from cloud_storage_oci import *
from logger import logger
from dotenv import load_dotenv

app = FastAPI(title="Sakhi API Service",
            #   docs_url=None,  # Swagger UI: disable it by setting docs_url=None
              redoc_url=None, # ReDoc : disable it by setting docs_url=None
              swagger_ui_parameters={"defaultModelsExpandDepth": -1},
              description='',
              version="1.0.0"
              )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info('Invoking startup_event')
    load_dotenv()
    logger.info('startup_event : Engine created')

@app.on_event("shutdown")
async def shutdown_event():
    logger.info('Invoking shutdown_event')
    logger.info('shutdown_event : Engine closed')


class FeedbackType(str, Enum):
    up = "up"
    down = "down"

class AudienceType(str, Enum):
    DEFAULT = "Default"
    TEACHER = "Teacher"
    PARENT = "Parent"

class Response(BaseModel):
    query: str = None
    answer: str = None
    source_text: str = None


class ResponseForAudio(BaseModel):
    query: str = None
    query_in_english: str = None
    answer: str = None
    answer_in_english: str = None
    audio_output_url: str = None
    source_text: str = None


class DropdownOutputFormat(str, Enum):
    TEXT = "Text"
    VOICE = "Voice"


class DropDownInputLanguage(str, Enum):
    en = "English"
    bn = "Bengali"
    gu = "Gujarati"
    hi = "Hindi"
    kn = "Kannada"
    ml = "Malayalam"
    mr = "Marathi"
    ori = "Oriya"
    pa = "Panjabi"
    ta = "Tamil"
    te = "Telugu"

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to Sakhi API Service"}

@app.get("/query-using-voice", tags=["Q&A over Document Store"],  include_in_schema=True)
async def query_with_voice_input(input_language: DropDownInputLanguage,
                                 output_format: DropdownOutputFormat, audience_type: AudienceType, query_text: str = "",
                                 audio_url: str = "") -> ResponseForAudio:
    load_dotenv()
    index_id = os.environ["MARQO_INDEX_NAME"]
    language = 'or' if input_language.name == DropDownInputLanguage.ori.name else input_language.name
    is_audio = False
    text = None
    paraphrased_query = None
    regional_answer = None
    answer = None
    audio_output_url = None
    source_text = None
    logger.info({"label": "query", "query_text":query_text, "index_id": index_id, "audience_type": audience_type, "input_language": input_language, "output_format": output_format, "audio_url": audio_url})
    if query_text == "" and audio_url == "":
        query_text = None
        error_message = "Either 'Query Text' or 'Audio URL' should be present"
        status_code = 422
    else:
        if query_text != "":
            text, error_message =   process_incoming_text(query_text, language)
            if output_format.name == "VOICE":
                is_audio = True
        else:
            query_text, text, error_message = process_incoming_voice(audio_url, language)
            is_audio = True

        if text is not None:
            answer, source_text, paraphrased_query, error_message, status_code = querying_with_langchain_gpt3(index_id, text)
            if len(answer) != 0:
                regional_answer, error_message = process_outgoing_text(answer, language)
                if regional_answer is not None:
                    if is_audio:
                        output_file, error_message = process_outgoing_voice(regional_answer, language)
                        print("Errrrr")
                        print(output_file, error_message)
                        if output_file is not None:
                            upload_file_object(output_file.name)
                            print("uploded")
                            audio_output_url, error_message = give_public_url(output_file.name)
                            logger.debug("Audio Ouput URL ===>", audio_output_url)
                            output_file.close()
                            os.remove(output_file.name)
                        else:
                            status_code = 503
                    else:
                        audio_output_url = ""
                else:
                    status_code = 503
        else:
            status_code = 503

    if source_text is not None:
        sources = get_source_markdown(source_text, language)
        regional_answer = (regional_answer or "") + sources
        answer = answer + sources

    if status_code != 200:
        logger.error({"uuid_number":index_id, "query":query_text, "input_language": input_language, "output_format": output_format, "audio_url": audio_url, "status_code": status_code, "error_message": error_message})
        raise HTTPException(status_code=status_code, detail=error_message)

    response = ResponseForAudio()
    response.query = query_text
    response.query_in_english = text
    response.answer = regional_answer
    response.answer_in_english = answer
    response.audio_output_url = audio_output_url
    response.source_text = ''
    logger.info(msg=response)
    return response