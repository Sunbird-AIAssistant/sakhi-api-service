# Activity Sakhi API : Factual Question & Answering over arbitrary number of documents

A powerful service designed to enhance the educational experience for both parents and teachers. Our service revolves around a curated collection of documents focused on children's activities and curriculum frameworks. With simplicity at its core, "Activity Sakhi" empowers parents and teachers to effortlessly discover relevant content and find answers to audience-specific questions.

### Key Features:
#### Rich Content Repository: 
Explore a predefined set of documents tailored to children's activities and curriculum frameworks, ensuring a wealth of valuable information at your fingertips.
#### Audience-Centric: 
Targeted specifically for parents and teachers, "Activity Sakhi" caters to their unique needs, providing insights and resources tailored to enhance the learning journey.
Discover and Learn: Seamlessly discover engaging content and obtain answers to your specific questions, making the educational process more accessible and enjoyable.

Whether you're a parent looking for creative activities or a teacher seeking curriculum support, Activity Sakhi is your go-to solution. Unlock the potential of educational resources and make learning a delightful experience for children.

### Getting Started:
Integrate "Activity Sakhi" effortlessly into your applications to revolutionize the way parents and teachers engage with educational content. Check out our documentation to get started and embark on a journey of enriched learning experiences.

### Prerequisites

- **Python 3.7 or higher**
- Latest Docker


### [Morqo database setup](https://docs.marqo.ai/1.5.0/#setup-and-installation)

1. To get the Morqo image, use the following command:

```shell
docker pull marqoai/marqo:latest
```

2. To create the Morqo instance, run the following command:

```shell
docker run --name marqo --privileged \
  -p 8882:8882 \
  --add-host host.docker.internal:host-gateway \
  -d marqoai/marqo:latest
```


# 🔧 1. Installation

To use the code, you need to follow these steps:

1. Clone the repository from GitHub: 
    
    ```bash
    git clone https://github.com/DJP-Digital-Jaaduii-Pitara/sakhi-api-service.git
    ```
   
    ```
   cd sakhi-api-service
   ```

2. The code requires **Python 3.7 or higher** and some additional python packages. To install these packages, run the following command in your terminal:

    ```bash
    pip install -r requirements-dev.txt
    ```

3. To injest data to marqo

    ```bash
    python3 index_documents.py --marqo_url=<MARQO_URL> --index_name=<MARQO_INDEX_NAME> --folder_path=<PATH_TO_INPUT_FILE_DIRECTORY>
    ```
   e.g.
   ```bash
   python3 index_documents.py --marqo_url=http://0.0.0.0:8882 --index_name=sakhi_activity --folder_path=input_data
   ```

4. You will need an OCI account to store the audio file for response.

5. create another file **.env** which will hold the development credentials and add the following variables. Update the openai_api_key, OCI details, Bhashini endpoint URL and API key.

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
    TELEMETRY_ENDPOINT_URL=<telemetry_url>
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

### `POST /v1/query`

#### API Function
API is used to generate activity/story based on user query and translation of text/audio from one language to another language in text/audio format. To achieve the same, Bhashini has been integrated. OCI object storage has been used to store translated audio files when audio is chosen as target output format.

```commandline
curl -X 'POST' \
  'http://127.0.0.1:8000/v1/query' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "input": {
    "language": "en",
    "text": "string",
    "audio": "string",
    "audienceType": "any"
  },
  "output": {
    "format": "text"
  }
}'
```

#### Request
| Request Input      |                                                       Value |
|:-------------------|----------------------------------|
| input.language     | en,bn,gu,hi,kn,ml,mr,or,pa,ta,te |
| input.text         | User entered question (any of the above language) |
| input.audio        | Public file URL Or Base64 encoded audio |
| input.audienceType | any, parent, teacher (default value is any, if not passing) |
| output.format      | text or audio |

Required inputs are 'text', 'audio' and 'language'.

Either of the 'text'(string) or 'audio'(string) should be present. If both the values are given, exception is thrown. Another requirement is that the 'language' should be same as the one given in text and audio (i.e, if you pass English as 'language', then your 'text'/'audio' should contain queries in English language). The audio should either contain a publicly downloadable url of mp3 file or base64 encoded text of the mp3.
If output format is given as 'text' than response will return text format only. If output format is given as 'audio' than response will return text and audio both.

```json
{
   "input": {
      "text": "How to Teach Kids to Play Games", 
      "language": "en"
   },
   "output": {
      "format": "text"
   }
}
```

#### Successful Response

```json
{
   "output": {
      "text": "string",
      "audio": "string",
      "language": "en",
      "format": "text|audio"
   }
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

 
