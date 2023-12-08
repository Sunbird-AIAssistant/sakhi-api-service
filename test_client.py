import requests

url = 'http://127.0.0.1:8000/query-with-langchain-gpt4_streaming'
params = {
    'uuid_number': '42d4634a-09c9-11ee-b47a-0d5cda16a4a6',
    'query_string': 'why QuML'
}
headers = {
    'Accept': 'text/plain'
}

# Send the GET request with the specified parameters and headers
response = requests.get(url, params=params, headers=headers, stream=True)

# Iterate through the response content as chunks are received
for chunk in response.iter_content(chunk_size=None):
    # Process each chunk as needed
    print(chunk.decode('utf-8'))  # Decode and print the chunk as a UTF-8 string
