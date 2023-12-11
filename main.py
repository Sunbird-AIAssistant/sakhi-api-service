import os.path
from enum import Enum
from cachetools import TTLCache
import secrets
from fastapi import Depends, FastAPI, UploadFile, File, HTTPException, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.status import HTTP_401_UNAUTHORIZED
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database_functions import *
from io_processing import *
from query_with_langchain import *
from cloud_storage_oci import *
import uuid
import shutil
from zipfile import ZipFile
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse
import time

api_description = ""

app = FastAPI(title="Jadui Sakhi Bot API",
            #   docs_url=None,  # Swagger UI: disable it by setting docs_url=None
              redoc_url=None, # ReDoc : disable it by setting docs_url=None
              swagger_ui_parameters={"defaultModelsExpandDepth": -1},
              description=api_description,
              version="1.0.0"
              )
ttl = int(os.environ.get("CACHE_TTL", 86400)) 
cache = TTLCache(maxsize=100, ttl=ttl)

security = HTTPBasic()
db_engine = None

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
    global db_engine  # Declare db_engine as global
    db_engine = await create_engine()
    logger.info('startup_event : Engine created')

@app.on_event("shutdown")
async def shutdown_event():
    logger.info('Invoking shutdown_event')
    load_dotenv()
    await db_engine.close()
    logger.info('shutdown_event : Engine closed')


class FeedbackType(str, Enum):
    up = "up"
    down = "down"

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
    hi = "Hindi"
    kn = "Kannada"

def get_current_username(
    credentials: HTTPBasicCredentials = Depends(security)
):
    load_dotenv()
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = bytes(os.environ.get("USERNAME"), 'utf-8')
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = bytes(os.environ.get("PASSWORD"), 'utf-8')
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Welcome to Jugalbandi API"}

@app.get("/query-using-voice", tags=["Q&A over Document Store"],  include_in_schema=True)
async def query_with_voice_input(input_language: DropDownInputLanguage,
                                 output_format: DropdownOutputFormat, query_text: str = "",
                                 audio_url: str = "") -> ResponseForAudio:
    load_dotenv()
    index_id = os.environ["MARQO_INDEX_NAME"]
    language = input_language.name
    output_medium = output_format.name
    is_audio = False
    text = None
    paraphrased_query = None
    regional_answer = None
    answer = None
    audio_output_url = None
    source_text = None

    if query_text == "" and audio_url == "":
        query_text = None
        error_message = "Either 'Query Text' or 'Audio URL' should be present"
        status_code = 422
    else:
        if query_text != "":
            text, error_message = process_incoming_text(query_text, language)
            if output_format.name == "VOICE":
                is_audio = True
        else:
            query_text, text, error_message = process_incoming_voice(audio_url, language)
            output_medium = "VOICE"
            is_audio = True

        if text is not None:
            answer, source_text, paraphrased_query, error_message, status_code = querying_with_langchain_gpt3(index_id, text)
            print(text, answer)
            if len(answer) != 0:
                regional_answer, error_message = process_outgoing_text(answer, language)
                if regional_answer is not None:
                    if is_audio:
                        output_file, error_message = process_outgoing_voice(regional_answer, language)
                        if output_file is not None:
                            upload_file_object(output_file.name)
                            audio_output_url = give_public_url(output_file.name)
                            print("audio_output_url ===>", audio_output_url)
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
        regional_answer = (regional_answer or "") + get_source_markdown(source_text, language)
        answer = answer + get_source_markdown(source_text, language)

    engine = await create_engine()
    await insert_qa_voice_logs(engine=engine, uuid_number=index_id, input_language=input_language.value,
                               output_format=output_medium, query=query_text, query_in_english=text,
                               paraphrased_query=paraphrased_query, response=regional_answer,
                               response_in_english=answer,
                               audio_output_link=audio_output_url, source_text=str(source_text), error_message=error_message)
    await engine.close()
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=error_message)

    response = ResponseForAudio()
    response.query = query_text
    response.query_in_english = text
    response.answer = regional_answer
    response.answer_in_english = answer
    response.audio_output_url = audio_output_url
    response.source_text = ''
    return response


@app.get("/rephrased-query", include_in_schema=False)
async def get_rephrased_query(query_string: str, username: str = Depends(get_current_username)):
    load_dotenv()
    answer = rephrased_question(query_string)
    return {"given_query": query_string, "rephrased_query": answer}
 
@app.get("/generate_answers", tags=["API for generating answers"], include_in_schema=True)
async def query_using_langchain_with_gpt3(query_string: str):
    load_dotenv()
    index_id = os.environ["MARQO_INDEX_NAME"]
    question_id = str(uuid.uuid1())
    answer, source_text, paraphrased_query, error_message, status_code = querying_with_langchain_gpt3(index_id, query_string)
    if source_text is not None:
            answer = answer + get_source_markdown(source_text)

    # engine = await create_engine()
    await insert_sb_qa_logs(engine=db_engine, model_name="gpt-3.5-turbo-16k", uuid_number=index_id, question_id=question_id,
                                            query=query_string, paraphrased_query=paraphrased_query, response=answer, source_text=str(source_text), error_message=error_message)
    # await engine.close()
    logger.info(f"Question ID =====> {question_id}")
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=error_message)

    response = {
        "id": question_id,
        "query": query_string,
        "answer": answer,
        "source_text" : ''
    }
    return response
        
    
@app.put("/user_feedback", tags=["API for recording user feedback for Q&A"], include_in_schema=False)
async def feedback_endpoint(question_id: str = Form(...), feedback_type: FeedbackType = Form(...), username: str = Depends(get_current_username)):
    load_dotenv()
    # engine = await create_engine()
    success_message, error_message, status_code = await record_user_feedback(db_engine, question_id, feedback_type.value)
    # await engine.close()
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=error_message)

    return {"message": f"Feedback recorded for question ID {question_id} with feedback type {feedback_type}"}