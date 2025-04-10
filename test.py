# from openai import AzureOpenAI
# from dotenv import load_dotenv
# import os

# load_dotenv()

# azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
# azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
# azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION")
# azure_chat_deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
# azure_embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME")

# azure_client = AzureOpenAI(
#         azure_endpoint=azure_endpoint,
#         api_key=azure_api_key,
#         api_version=azure_api_version
#     )

# response = azure_client.chat.completions.create(
#         model=azure_chat_deployment,
#         messages=[
#             {"role": "system", "content": "You are an expert recruitment assistant helping to explain job matches."},
#             {"role": "user", "content": "Hi"}
#         ],
#         temperature=0.5,
#         max_tokens=120
#     )

# embedding_client = AzureOpenAI(
#     azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
#     azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
#     api_key=os.getenv("EMBEDDING_CLIENT_API_KEY"),
#     api_version="2023-05-15",
# )

# text = "hello"
# response = embedding_client.embeddings.create(input=text, model=azure_embedding_deployment)
# print(response.data[0].embedding)

# # justification = response.choices[0].message.content.strip()
# # print(justification)


# from nltk.tokenize import word_tokenize
# from nltk.corpus import stopwords

# def preprocess_text_for_bm25(text):
#     """Basic text cleaning and tokenization for BM25."""
#     if not isinstance(text, str):
#         return []
#     text = text.lower()
#     text = re.sub(r'[^\w\s]', '', text) # Remove punctuation
#     tokens = word_tokenize(text, language='english', preserve_line=True)
#     tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
#     return tokens