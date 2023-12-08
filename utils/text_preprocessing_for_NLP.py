# Text pre-processing: Stop words removal using nltk library
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download the necessary NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

def preprocess_text(text):
    """Performs basic text preprocessing.

    Args:
        text (str): The text to preprocess.

    Returns:
        str: The preprocessed text.
    """

    # Tokenize the text
    tokens = word_tokenize(text)

    # Convert the text to lowercase
    tokens = [token.lower() for token in tokens]

    # Remove punctuation
    # tokens = [token for token in tokens if token.isalnum()]

    # Remove stop words
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words]

    # Return the preprocessed text
    return " ".join(tokens)


input_text = ''
preprocessed_text = preprocess_text(input_text)
print(preprocessed_text)

