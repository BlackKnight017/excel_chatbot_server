from fastapi import FastAPI, Request

from langchain import OpenAI, SQLDatabase , SQLDatabaseChain
from langchain.chat_models import ChatOpenAI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import openai
import os


load_dotenv()

database = os.getenv("DB")
host = os.getenv("HOST")
user = os.getenv("USER")
password = os.getenv("PASSWORD")
port = os.getenv("PORT")

openai_key = os.getenv("OPENAI_API_KEY")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Define SQLDatabaseChain

llm = ChatOpenAI(model_name='gpt-3.5-turbo', openai_api_key=openai_key, temperature=0.3)

current_path = os.path.dirname(__file__)
# dburi = os.path.join('sqlite:///' + current_path,
#                      "db", "output.db")
# db = SQLDatabase.from_uri(dburi)

db = SQLDatabase.from_uri(f"postgresql://{user}:{password}@{host}:{port}/{database}", include_tables=['Report_data'])

db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True, return_intermediate_steps=True, top_k = 30)

# Connect to the database
def remove_word(sentence, target_word):
    words = sentence.split()
    cleaned_words = [word for word in words if not target_word in word]
    cleaned_sentence = ' '.join(cleaned_words)
    return cleaned_sentence





app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/hello/")
def read_root():
    return "Hello World"



@app.post("/chat/")
async def chat(reqeust: Request):

    body = await reqeust.json()
    query = body['query']
    
    if "% stage" in query:
        query = remove_word(query, "stage")
        
    additional_query = """
        If the question has any data about date, consider only this month.
        If the question has any additional information, consider the sum.
        If the question includes only "value", not "Expected value", consider column `Pipeline Part Value`, not column `Expected Revenue`.
        If only the question includes "stage", should consider column `Stage`.
        In the question, `Pipeline` has not relationship with column `Stage`, so SQL Query should not contain "Stage" = "Pipeline".
        First, should make correct SQL Query depends on question.
        No LIMIT, should include all possible records.
        Based on above question, SQL Query and SQL Result, make clear, correct final answer.
        Final Answer should contain all SQL Results.
        Final Answer should be structured.
    """
    query += additional_query
    res = db_chain(query)
    steps = res['intermediate_steps']
    
    return {"message" : res['result']}

