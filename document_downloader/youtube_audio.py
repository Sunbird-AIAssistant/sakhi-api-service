import yt_dlp

class YoutubeAudioDownloader:
    """Load YouTube urls as audio file(s)."""
    def __init__(self, save_dir: str):
        """
        Initializes the YoutubeAudioDownloader with the specified output directory.

        Args:
            save_dir (str): The directory where downloaded audio files will be saved.
        """
        self.save_dir = save_dir
         # Use yt_dlp to download audio given a YouTube url
        self.ydl_opts = {
            "format": "m4a/bestaudio/best", # Download the best available audio format
            "noplaylist": True,
            # "quiet": True,
            "outtmpl": self.save_dir + "/%(title)s.%(ext)s", # Output template with clear path
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio", # Extract audio using FFmpeg
                    "preferredcodec": "mp3"
                }
            ],
        }
    

    def download_audio(self, url: str) -> None:
        """
        Downloads the audio file for the provided YouTube URL.

        Args:
            url (str): The URL of the YouTube video to download audio from.

        Raises:
            yt_dlp.utils.DownloadError: If an error occurs during the download process.
        """

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            ydl.download(url)
             # Downloaded file path based on write_filename
            downloaded_filepath = ydl.prepare_filename(ydl.extract_info(url, download=False))
        return downloaded_filepath.replace(".m4a", ".mp3") if downloaded_filepath else None