from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize Azure OpenAI Client
try:
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    azure_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    azure_openai_embedding_endpoint = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
    azure_openai_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")
    azure_openai_embedding_api_key = os.getenv("EMBEDDING_CLIENT_API_KEY")

    if not all([azure_endpoint, azure_api_key, azure_api_version, azure_chat_deployment, azure_openai_embedding_endpoint, azure_openai_embedding_deployment, azure_openai_embedding_api_key]):
        raise ValueError("Missing one or more Azure OpenAI environment variables.")

    azure_client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        api_key=azure_api_key,
        api_version=azure_api_version
    )

    embedding_client = AzureOpenAI(
        azure_endpoint=azure_openai_embedding_endpoint,
        azure_deployment=azure_openai_embedding_deployment,
        api_key=azure_openai_embedding_api_key,
        api_version="2023-05-15",
    )
    
    # Test connection (optional)
    azure_client.models.list()
    print("Azure OpenAI client initialized successfully.")
except Exception as e:
    print(f"Error initializing Azure OpenAI client: {e}")
    print("Please ensure AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_CHAT_DEPLOYMENT_NAME, and AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME are set correctly in your environment or .env file.")
    exit()