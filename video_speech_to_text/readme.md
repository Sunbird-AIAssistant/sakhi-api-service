# Video Speech to Text

This script will generate transcript files from multiple video files using OpenAI Whisper.

## Requirements:

- Python 3.6+
- OpenAI Whisper API

## Usage:

- Install Python 3.6+ and the OpenAI Whisper API.
- Run the following command:
    `python video_speech_to_text.py`
- Enter the video directory path when prompted.
- The script will create an output folder named transcript_output containing all transcript files.

This script can be used to generate transcripts for multiple video files in a directory. The output transcripts will be saved in an output folder named transcript_output.

### Example:

```
python video_speech_to_text.py

Enter video directory path: /path/to/videos

...

Transcript files generated successfully.
```

### Notes:

- The OpenAI Whisper API is a paid service. You will need to create an account and obtain an API key to use the API.
- The script will generate transcript files in the same directory as the video files, unless you specify a different output directory.
- The script will generate transcript files for all video files in the specified directory. If you only want to generate transcript files for specific video files, you can move those files to a separate directory and specify that directory as the input directory.


## Convert audio to text
https://github.com/openai/whisper


