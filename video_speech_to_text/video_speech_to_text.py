import os
import moviepy.editor as mp
import subprocess
import shutil

def extract_audio_from_video(video_file, audio_file):
    # Load the video
    video = mp.VideoFileClip(video_file)

    # Extract the audio from the video
    audio = video.audio
    audio.write_audiofile(audio_file)
    
    print(f"Done extracting audio from video {video_file}: {audio_file}")


def transcribe_audio_using_whisper(audio_file, video_filename, output_directory):
    # Change the current working directory to the output_directory
    # os.chdir(output_directory)
    
    # Construct the command to transcribe audio using whisper
    command = f"whisper {audio_file} --model tiny --language Hindi --output_dir {output_directory} --output_format txt"
    
    try:
        subprocess.run(command, shell=True, check=True)

        print(f"Done extracting text from audio {command} : for the video file {video_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error while transcribing {video_filename}: {e} : Command Run {command}")

    # Change the current working directory back to the original directory
    # os.chdir("..")  # Assuming you want to move back to the parent directory

# def transcribe_audio(audio_file):
#     # Initialize recognizer
#     r = sr.Recognizer()

    # Load the audio file
#     with sr.AudioFile(audio_file) as source:
#         data = r.record(source, duration=300)

    # Convert speech to text using Google Web API (requires internet connection)
#    try:
#        text = r.recognize_google(data)
#        return text
#    except sr.UnknownValueError:
#        return "Could not understand audio"
#    except sr.RequestError:
#        return "Could not request results; check your network connection"


def process_video_list(directory_path):
    # List all the files and directories in the directory
    files = os.listdir(directory_path)

    # Filter the list of files to only include files
    files = [file for file in files if os.path.isfile(os.path.join(directory_path, file))]

    for video_file in files:
        print(video_file)
        video_filename = os.path.basename(video_file)
        file_name_extracted = os.path.splitext(video_filename)[0]  # Remove file extension

        print(f"Input received for transcribing {video_filename}: {file_name_extracted}")

        video_file_path = os.path.join(directory_path, video_file)

        # Ensure the directory name doesn't contain special characters or spaces
        audio_output_file_name = ''.join(e for e in file_name_extracted if e.isalnum() or e == "_")


        # Create a new temporary directory
        temp_dir = 'tmp'
        os.makedirs(temp_dir, exist_ok=True)

        audio_file = os.path.join(temp_dir, f"{audio_output_file_name}.wav")
        extract_audio_from_video(video_file_path, audio_file)
        print(f"Output audio file is names as {audio_file}")

        # Uncommenting the following line to transcribe audio using Whisper
        # text = transcribe_audio(audio_file)

        # Create a new output directory called "output"
        transcript_output_dir = "transcript_output"
        os.makedirs(transcript_output_dir, exist_ok=True)

        # Transcribe audio using the Whisper command-line call
        transcribe_audio_using_whisper(audio_file, video_filename, transcript_output_dir)

        # Print the transcribed text (commented as per your request)
        # print(f"\nThe resultant text from {video_filename} is:\n")
        # print(text)

    shutil.rmtree(temp_dir)
    print("Transcript files generated successfully.")

    
if __name__ == "__main__":
    
    # Get the video directory path
    input_dir = input("Enter video direcotory path: ")
    if not input_dir:
        raise Exception("Please provide input direcotory path")

    print(f"Input Directory: {input_dir}")

    process_video_list(input_dir)

