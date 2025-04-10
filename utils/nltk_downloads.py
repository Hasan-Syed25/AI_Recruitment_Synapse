from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk

try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Downloading NLTK data (punkt, stopwords)...")
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab')
    print("NLTK data downloaded.")