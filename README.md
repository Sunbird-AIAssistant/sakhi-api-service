# Jugalbandi API : Factual Question & Answering over arbitrary number of documents

[Jugalbandi API](https://api.jugalbandi.ai/docs) is a system of APIs that allows users to build Q&A style applications on their private and public datasets. The system creates Open API 3.0 specification endpoints using FastAPI.


# 🔧 1. Installation

To use the code, you need to follow these steps:

1. Clone the repository from GitHub: 
    
    ```bash
    git clone https://github.com/DJP-Digital-Jaaduii-Pitara/sakhi-api-service.git
    ```

2. The code requires **Python 3.7 or higher** and some additional python packages. To install these packages, run the following command in your terminal:

    ```bash
    pip install -r requirements-dev.txt
    ```

3. You will need a OCI account to store the audio file for response & marqo vector database for semantic similarity search.

4. create another file **.env** which will hold the development credentials and add the following variables. Update the openai_api_key, OCI details, Bhashini endpoint URL and API key.

    ```bash
    SERVICE_ENVIRONMENT=<name_of_the_environment>
    OPENAI_API_KEY=<your_openai_api_key>
    LOG_LEVEL=<log_level>  # INFO, DEBUG, ERROR
    BHASHINI_ENDPOINT_URL=<your_bhashini_api_endpoint>
    BHASHINI_API_KEY=<your_bhashini_api_key>
    OCI_ENDPOINT_URL=<oracle_bucket_name>
    OCI_REGION_NAME=<oracle_region_name>
    OCI_BUCKET_NAME=<oracle_bucket_name>
    OCI_SECRET_ACCESS_KEY=<oracle_secret_access_key>
    OCI_ACCESS_KEY_ID=<oracle_access_key_id>
    MARQO_URL=<your_marqo_db_url>
    MARQO_INDEX_NAME=<your_marqo_index_name>
    TELEMETRY_ENDPOINT_URL=<telemetry_endpoint_url>
    ```

# 🏃🏻 2. Running

Once the above installation steps are completed, run the following command in home directory of the repository in terminal

```bash
uvicorn main:app
```
Open your browser at http://127.0.0.1:8000/docs to access the application.

The command `uvicorn main:app` refers to:

- `main`: the file `main.py` (the Python "module").
- `app`: the object created inside of `main.py` with the line `app = FastAPI()`.
- `--reload`:  make the server restart after code changes. Only do this for development.
    ```bash
    uvicorn main:app --reload
    ```

When you try to open the URL for the first time (or click the "Execute" button in the docs) the browser will ask you for your username and password (Which you provided in the `.env` file):

![Alt text](docs/image.png)

# 📃 3. API Specification and Documentation

### `GET /query-using-voice`

#### Request

Requires an input_language(Selection - English, Hindi, Kannada, etc..), audience_type(Selection - Default, Teacher, Parent) and output_format(Selection - Text, Voice).

Either of the query_text(string) or audio_url(string) should be present. If both the values are given, query_text is taken for consideration. Another requirement is that the input_language should be same as the one given in query_text and audio_url (i.e, if you select English in input_language, then your query_text and audio_url should contain queries in English). The audio_url should be publicly downloadable, otherwise the audio_url will not work.

#### Successful Response

```json
{
  "query": "<query-in-given-language>",
  "query_in_english": "<query-in-english>",
  "answer": "<paraphrased-answer-in-given-language>",
  "answer_in_english": "<paraphrased-answer-in-english>",
  "audio_output_url": "<publicly-downloadable-audio-output-url-in-given-language>",
  "source_text": "<source-text-from-which-answer-is-paraphrased-in-english>"
}
```

#### What happens during the API call?

Once the API is hit with proper request parameters, it is then checked for the presence of query_text. 

If query_text is present, the translation of query_text based on input_language is done. Then the translated query_text is given to langchain model which does the same work. Then the paraphrased answer is again translated back to input_language. If the output_format is voice, the translated paraphrased answer is then converted to a mp3 file and uploaded to a OCI folder and made public.

If the query_text is absent and audio_url is present, then the audio url is downloaded and converted into text based on the input_language. Once speech to text conversion in input_language is finished, the same process mentioned above happens. One difference is that by default, the paraphrased answer is converted to voice irrespective of the output_format since the input_format is voice.

# 🚀 4. Deployment

This repository comes with a Dockerfile. You can use this dockerfile to deploy your version of this application to Cloud Run.
Make the necessary changes to your dockerfile with respect to your new changes. (Note: The given Dockerfile will deploy the base code without any error, provided you added the required environment variables (mentioned in the .env file) to either the Dockerfile or the cloud run revision)


## Feature request and contribution

*   We are currently in the alpha stage and hence need all the inputs, feedbacks and contributions we can.
*   Kindly visit our project board to see what is it that we are prioritizing.

 
