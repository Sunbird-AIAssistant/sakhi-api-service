from abc import ABC, abstractmethod
from typing import Any

class BaseTranslationClass(ABC):
    """
    This abstract class defines the interface for a translation service.

    Subclasses must implement the abstract methods to provide specific translation functionality.
    """

    def __init__(self):
        pass

    @abstractmethod
    def translate_text(self, text: str, source: str, destination: str):
        """
        This method translates a text string to another language.

        Args:
            text: The text string to be translated (str).

        Returns:
            The translated text string.

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """

    @abstractmethod
    def text_to_speech(self, language: str, text: str) -> Any:
        """
        This method converts text to speech in a specified language.

        The specific return type (e.g., audio data) depends on the subclass implementation.

        Args:
            language: The target language for the speech (str).
            text: The text to be converted to speech (str).

        Returns:
            The speech representation of the text (type varies depending on subclass).

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """

    @abstractmethod
    def speech_to_text(self, audio_file: Any, input_language: str):
        """
        This method converts speech from an audio file to text.

        The specific format of the audio_file argument depends on the subclass implementation.

        Args:
            audio_file: The audio file containing the speech (type varies depending on subclass).
            input_language: The language of the speech in the audio file (str).

        Returns:
            The transcribed text from the audio file (str).

        Raises:
            NotImplementedError: If the subclass does not implement this method.
        """