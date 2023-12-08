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

3. You will need a GCP account to store the uploaded documents & indices in a bucket and to host a postgres connection to store the api logs.

4. Navigate to the repository directory. Create a file named **gcp_credentials.json** which will contain the service account credentials of your GCP account. The file will roughly have the same format mentioned below.

    ```bash
    {
      "type": "service_account",
      "project_id": "<your-project-id>",
      "private_key_id": "<your-private-key-id>",
      "private_key": "<your-private-key>",
      "client_email": "<your-client-email>",
      "client_id": "<your-client-id>",
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": "<your-client-cert-url>"
    }
    ```

5. In addition to creating gcp_credentials.json file, create another file **.env** which will hold the development credentials and add the following variables. Update the openai_api_key, path to gcp_credentials.json file, gcp_bucket_name and your db connections appropriately.

    ```bash
    OPENAI_API_KEY=<your_openai_api_key>
    GOOGLE_APPLICATION_CREDENTIALS=<path-to-gcp_credentials.json>
    BUCKET_NAME=<your_gcp_bucket_name>
    DATABASE_NAME=<your_db_name>
    DATABASE_USERNAME=<your_db_username>
    DATABASE_PASSWORD=<your_db_password>
    DATABASE_IP=<your_db_public_ip>
    DATABASE_PORT=5432
    USERNAME=<your_login_username>
    PASSWORD=<your_login_password>
    AI4BHARAT_API_KEY=<your_ai4bharat_api_key>
    MARQO_URL=<your_marqo_db_url>
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


### `POST /upload-files`

Returns an UUID number for a set of documents uploaded

#### Request

Requires a description(string) and at least one file(currently only PDF & txt files) for uploading.

#### Successful Response

```json
{
   "uuid_number": "<36-character string>", 
   "message": "Files uploading is successful"
}
```

#### What happens during the API call?

Once the API is hit with proper request parameters, an uuid_number is created and the files are uploaded to the GCP bucket with the uuid_number as folder name. Immediately after this process, indexing of the files happen. Two types of indexing happen - one for gpt-index and the other for langchain. The two indexing processes produce three index files - index.json, index.faiss and index.pkl. These index files are again uploaded to the same GCP bucket folder for using them during query time.

---

### `GET /query-with-gptindex`

#### Request

Requires an uuid_number(string) and query_string(string).

#### Successful Response

```json
{
  "query": "<your-given-query>",
  "answer": "<paraphrased-response>",
  "source_text": "<source-text-from-which-answer-is-paraphrased>"
}
```

#### What happens during the API call?

Once the API is hit with proper request parameters, the **index.json** file is fetched from the GCP bucket provided the uuid_number given is correct. Once the **index.json** is successfully fetched, it is then used to answer the query given by the user.

---

### `GET /query-with-langchain` (Same as /query-with-gptindex)

#### Request

Requires an uuid_number(string) and query_string(string).

#### Successful Response

```json
{
  "query": "<your-given-query>",
  "answer": "<paraphrased-response>",
  "source_text": "<source-text-from-which-answer-is-paraphrased>"
}
```

#### What happens during the API call?

Once the API is hit with proper request parameters, the **index.faiss** and **index.pkl** files are fetched from the GCP bucket provided the uuid_number given is correct. Once the index files are successfully fetched, they are then used to answer the query given by the user.

---

### `GET /query-using-voice`

#### Request

Requires an index_id(string), input_language(Selection - English, Hindi, Kannada) and output_format(Selection - Text, Voice).

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

If query_text is present, the translation of query_text based on input_language is done. Then the translated query_text is given to langchain model which does the same work as `/query-with-langchain` endpoint. Then the paraphrased answer is again translated back to input_language. If the output_format is voice, the translated paraphrased answer is then converted to a mp3 file and uploaded to a GCP folder and made public.

If the query_text is absent and audio_url is present, then the audio url is downloaded and converted into text based on the input_language. Once speech to text conversion in input_language is finished, the same process mentioned above happens. One difference is that by default, the paraphrased answer is converted to voice irrespective of the output_format since the input_format is voice.

---


### `GET /query-with-langchain-gpt4` (Same as /query-with-langchain)

#### Request

Requires an uuid_number(string) and query_string(string).

#### Successful Response

```json
{
  "query": "<your-given-query>",
  "answer": "<response>",
  "source_text": ""
}
```

#### What happens during the API call?

Once the API is hit with proper request parameters, the **index.faiss** and **index.pkl** files are fetched from the GCP bucket provided the uuid_number given is correct. Once the index files are successfully fetched, they are then used to answer the query given by the user.

One major difference here is that this api uses GPT4 model for querying process, hence the answer will not be paraphrased on most cases and precisely that is why the source_text will be empty in the response since we get the actual source_text present in the document as the answer in response.

---

### `GET /query-with-langchain-gpt4-mcq`

#### Request  

QUERY PARAMETERS

  1. uuid_number (string) - required
  2. query_string (string) - required
  3. caching (boolen) - required

The UUID number has been classified into two categories:
- **Technology Specific:** Pass `tech` instead of the UUID number when you want to generate technology-specific questions.
- **Domain Specific:** Requires the actual UUID number where the document was uploaded.


#### Successful Response

```json
{
  "query": "<your-given-query>",
  "answer": "<response>",
  "source_text": ""
}
```

#### What happens during the API call?

Once the API is hit with proper request parameters, the **index.faiss** and **index.pkl** files are fetched from the GCP bucket provided the uuid_number given is correct. Once the index files are successfully fetched, they are then used to answer the query given by the user.

One major difference here is that this api uses GPT4 model for querying process, hence the answer will not be paraphrased on most cases and precisely that is why the source_text will be empty in the response since we get the actual source_text present in the document as the answer in response.

---

# 🚀 4. Deployment

This repository comes with a Dockerfile. You can use this dockerfile to deploy your version of this application to Cloud Run.
Make the necessary changes to your dockerfile with respect to your new changes. (Note: The given Dockerfile will deploy the base code without any error, provided you added the required environment variables (mentioned in the .env file) to either the Dockerfile or the cloud run revision)

# 👩‍💻 5. Usage

To directly use the Jugalbandi APIs without cloning the repo, you can follow below steps to get you started:

1.  Visit [https://api.jugalbandi.ai/docs](https://api.jugalbandi.ai/docs).
2.  Scroll to the `/upload-files` endpoint to upload the documents.
3.  Once you have uploaded file(s) you should have received a `uuid number` for that document set. Please keep this number handy as it will be required for you to query the document set.
4.  Now that you have the `uuid number` you should scroll up to select the query endpoint you want to use. Currently, there are three different implementations we support i.e. `query-with-gptindex`, `query-with-langchain` (recommended), `query-using-voice` (recommended for voice interfaces). While you can use any of the query systems, we are constantly refining our langchain implementation.
5.  Use the `uuid number` and do the query.

## Feature request and contribution

*   We are currently in the alpha stage and hence need all the inputs, feedbacks and contributions we can.
*   Kindly visit our project board to see what is it that we are prioritizing.

 
