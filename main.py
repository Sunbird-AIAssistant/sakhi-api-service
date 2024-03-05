import os
import json

from fastapi import FastAPI, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# from cloud_storage_oci import *
from storage.api import *
from io_processing import *
# from query_with_langchain import *
from query_with_langchain import *
from telemetry_middleware import TelemetryMiddleware
from config_util import get_config_value
from utils import *

from dotenv import load_dotenv

app = FastAPI(title="Sakhi API Service",
              #   docs_url=None,  # Swagger UI: disable it by setting docs_url=None
              redoc_url=None,  # ReDoc : disable it by setting docs_url=None
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


class OutputResponse(BaseModel):
    text: str
    audio: str = None
    language: str = None
    format: str = None


class ResponseForQuery(BaseModel):
    output: OutputResponse


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


class QueryInputModel(BaseModel):
    language: str = None
    text: str = None
    audio: str = None
    audienceType: str = None


class QueryOuputModel(BaseModel):
    format: str = None


class QueryModel(BaseModel):
    input: QueryInputModel
    output: QueryOuputModel


# Telemetry API logs middleware
app.add_middleware(TelemetryMiddleware)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to Sakhi API Service"}


@app.get(
    "/health",
    tags=["Health Check"],
    summary="Perform a Health Check",
    response_description="Return HTTP Status Code 200 (OK)",
    status_code=status.HTTP_200_OK,
    response_model=HealthCheck,
    include_in_schema=True
)
def get_health() -> HealthCheck:
    """
    ## Perform a Health Check
    Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
    to ensure a robust container orchestration and management is in place. Other
    services which rely on proper functioning of the API service will not deploy if this
    endpoint returns any other HTTP status code except 200 (OK).
    Returns:
        HealthCheck: Returns a JSON response with the health status
    """
    return HealthCheck(status="OK")


@app.post("/v1/query", tags=["Q&A over Document Store"], include_in_schema=True)
async def query(request: QueryModel, x_request_id: str = Header(None, alias="X-Request-ID")) -> ResponseForQuery:
    load_dotenv()

    language_code_list = get_config_value('request', 'supported_lang_codes', None).split(",")
    if language_code_list is None:
        raise HTTPException(status_code=422, detail="supported_lang_codes not configured!")

    language = request.input.language.strip().lower()
    if language is None or language == "" or language not in language_code_list:
        raise HTTPException(status_code=422, detail="Unsupported language code entered!")

    audience_type = request.input.audienceType
    if audience_type is None or audience_type.strip() == "":
        raise HTTPException(status_code=422, detail="Please pass audience type!")
    indices = json.loads(get_config_value('database', 'indices', None))
    index_id = indices.get(audience_type.lower())
    if index_id is None:
        raise HTTPException(status_code=422, detail="Unsupported audience type!")

    output_format_list = get_config_value('request', 'support_response_format', None).split(",")
    if output_format_list is None:
        raise HTTPException(status_code=422, detail="support_response_format not configured!")

    output_format = request.output.format.strip().lower()

    if output_format is None or output_format == "" or output_format not in output_format_list:
        raise HTTPException(status_code=422, detail="Invalid output format!")

    audio_url = request.input.audio
    query_text = request.input.text
    is_audio = False
    text = None
    regional_answer = None
    audio_output_url = None
    logger.info({"label": "query", "query_text": query_text, "index_id": index_id, "audience_type": audience_type, "input_language": language, "output_format": output_format, "audio_url": audio_url})

    if query_text is None and audio_url is None:
        raise HTTPException(status_code=422, detail="Either 'text' or 'audio' should be present!")
    elif (query_text is None or query_text == "") and (audio_url is None or audio_url == ""):
        raise HTTPException(status_code=422, detail="Either 'text' or 'audio' should be present!")
    elif query_text is not None and audio_url is not None and query_text != "" and audio_url != "":
        raise HTTPException(status_code=422, detail="Both 'text' and 'audio' cannot be taken as input! Either 'text' "
                                                    "or 'audio' is allowed.")

    if query_text:
        text, error_message = process_incoming_text(query_text, language)
        if output_format == "audio":
            is_audio = True
    else:
        if not is_url(audio_url) and not is_base64(audio_url):
            logger.error(
                {"index_is": index_id, "query": query_text, "input_language": language, "output_format": output_format, "audio_url": audio_url, "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY, "error_message": "Invalid audio input!"})
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid audio input!")
        query_text, text, error_message = process_incoming_voice(audio_url, language)
        is_audio = True
    logger.info({"Query": text})
    if text is not None:
        answer, error_message, status_code = querying_with_langchain_gpt3(index_id, text, audience_type)

        if len(answer) != 0:
            regional_answer, error_message = process_outgoing_text(answer, language)
            logger.info({"regional_answer": regional_answer})
            if regional_answer is not None:
                if is_audio:
                    output_file, error_message = process_outgoing_voice(regional_answer, language)
                    if output_file is not None:
                        upload_file_object(output_file.name)
                        audio_output_url, error_message = give_public_url(output_file.name)
                        logger.debug(f"Audio Ouput URL ===> {audio_output_url}")
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

    if status_code != 200:
        logger.error({"index_id": index_id, "query": query_text, "input_language": language, "output_format": output_format, "audio_url": audio_url, "status_code": status_code, "error_message": error_message})
        raise HTTPException(status_code=status_code, detail=error_message)

    response = ResponseForQuery(output=OutputResponse(text=regional_answer, audio=audio_output_url, language=language, format=output_format))
    logger.info({"x_request_id": x_request_id, "query": query_text, "text": text, "response": response})
    return response
