from dotenv import load_dotenv
load_dotenv()
from langchain_chroma import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.schema import Document
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
import os
import json
from langchain.retrievers import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.prompts import PromptTemplate
embedding = AzureOpenAIEmbeddings(azure_deployment="upcoretext-embedding")
persist_directory = "./UserVectordb"
db = Chroma(persist_directory=persist_directory, embedding_function=embedding)
llm = AzureChatOpenAI(
   azure_deployment="gpt-4o",
   model="gpt-4o",
   api_version="2023-03-15-preview",
#    streaming=True,
#    callbacks=[StreamingStdOutCallbackHandler()]
)

def vector_retriever():
    vectorstore_retriever = db.as_retriever(search_kwargs={"k": 100})
    return vectorstore_retriever
def bm25_retriever():
    # Fetch data from Chroma
    data = db.get()
    # Convert strings to Document objects
    documents = [Document(page_content=text) for text in data]
    # Create the BM25Retriever from the Document objects
    keyword_retriever = BM25Retriever.from_documents(documents)
    keyword_retriever.k = 100    
    return keyword_retriever
# def self_query_retriever():
#     metadata_field_info = [
#         AttributeInfo(name="user_name", description="The name of the user who made the call", type="string"),
#         AttributeInfo(name="text", description="The content of the chat message, including details of calls and tasks", type="string"),
#         AttributeInfo(name="channel_name", description="The channel where the message was posted", type="string"),
#         AttributeInfo(name="date", description="The date when the chat message was sent", type="date"),
#         AttributeInfo(name="organization_name", description="The name of the organization the user belongs to", type="string")
#     ]

#     prompt_template = PromptTemplate(input_variables=["query"], template= "Based on the user query, create a filter to retrieve relevant chat data.\n"
#         "Make sure to consider any specific entities, dates, users, or channels mentioned in the query.\n"
#         "User Query: {query}")

#     self_query_retriever = SelfQueryRetriever.from_llm(
#         llm=llm,
#         vectorstore=db,
#         document_contents="Call details and performance based on team chat",
#         metadata_field_info=metadata_field_info,
#         prompt_template=prompt_template,
#         search_kwargs={"k": 70}
#     )

#     return self_query_retriever
ensemble_retriever = EnsembleRetriever(retrievers=[bm25_retriever(), vector_retriever()], weights=[0.3, 0.3])
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
# Initialize the Azure OpenAI model

# Contextualize question system prompt
contextualize_q_system_prompt = """Given a chat history and the most recent user question, which may reference
the previous conversation, reformulate the question into a clear, standalone version that directly references the
 user's data for the specified time period (e.g., the week). Ensure the reformulated question is specific and understandable 
 without the chat history. If the question is already clear and independent, return it as is."""

# contextualize_q_system_prompt = """
# Given a chat history and the most recent user question, your task is to:

# 1. Detect if the question is referencing a specific entity or topic from the previous conversation (e.g., a person, task, or subject). If so, reformulate the question into a standalone version that includes this context explicitly.

# 2. **If the question asks for information about "all team members", ensure you reformulate it to request data for all users, aggregating the result if necessary.**

# 3. If the question is already clear and independent of the chat history, return it as is without modification.

# Ensure the reformulated question is self-contained, concise, and maintains the original meaning and intent.
# """


# Create the contextualize question prompt template
contextualize_q_prompt = ChatPromptTemplate(
[
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
# Create the history-aware retriever
history_aware_retriever = create_history_aware_retriever(
    llm,
    ensemble_retriever,  # Corrected typo here
    contextualize_q_prompt
)
# Define the QA template
template_for_reply="""
You are a chat assistant tasked with analyzing chat history and answering questions based on that history.
Your answers must be COMPREHENSIVE and INFORMATIVE leveraging the power of similar conversations from the Slack channel.
You must answer using the PROVIDED CONTEXT, ensuring a deep understanding of the context to deliver the best possible response.
Use all page content for your final answer.
Do not answer unrelated context.
* **Previous Context:**
{context}
* **Additional Context:**
* **PDF details:**
Drawing insights from these similar conversations, here's my answer:
"""
# Create the QA prompt template
qa_prompt = ChatPromptTemplate(
    [
       ("system", template_for_reply),
         MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
# Create the question-answering chain
question_answer_chain = create_stuff_documents_chain(
    llm,
    qa_prompt
)
# Create the RAG chain
rag_chain = create_retrieval_chain(
    history_aware_retriever ,
question_answer_chain
)
# In-memory store to manage session histories
store = {}
session_titles = {}

# Function to get or create session history
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()        
    return store[session_id]
# Wrap the RAG chain with message history management
conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history",
    output_messages_key="answer",
)
import os
import json
import logging
from datetime import datetime
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from sql_connect.main import insert_sessionllm_data

# Initialize variables for query and response
human_query = ""
ai_response = ""

def generate_session_title(session_id: str, initial_query: str) -> str:
    prompt = f"""Based on the initial query: "{initial_query}"
    Generate a short, descriptive title for this chat session.
    The title should be concise (max 5 words) and reflect the main topic or intent of the query.
    Return only the title, without any additional text or punctuation."""

    response = llm.invoke(prompt)
    
    title =   response.content 
    title = ' '.join(title.split()[:5])
    
    return title
# Function to save a message (insert directly into the database)
def save_message(session_id: str, role: str, content: str):
    global human_query, ai_response
    
    # Determine if it's a human query or AI response
    if role == "human":
        human_query = content
        # Generate title for the first human message in a session
        if session_id not in session_titles:
            session_titles[session_id] = generate_session_title(session_id, content)
    elif role == "ai":
        ai_response = content
    
    # Insert the message into the database when both human query and AI response are available
    if human_query and ai_response:
        # Insert into the sessionllm table
        db_name = 'slackpoc'
        session_name = session_titles.get(session_id, f"Unnamed Session {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        insert_sessionllm_data(db_name, session_id, session_name, human_query, ai_response)
        
        # Reset the queries after insertion
        human_query = ""
        ai_response = ""
# Function to load session history from the database (no more JSON file usage)
def load_session_history(session_id: str) -> BaseChatMessageHistory:
    chat_history = ChatMessageHistory()
    # Here, you would query the database for session history based on `session_id`
    # and populate `chat_history` object.
    # For now, we assume you already have a `load_session_data_from_db` function.
    
    session_name = f"session_{session_id}"  # Define session name format
    
    # Pseudo code to retrieve the data from the database (you'll need to implement this)
    # history_data = load_session_data_from_db(session_name)
    
    # Example:
    # for message in history_data:
    #     chat_history.add_message({"role": message["role"], "content": message["content"]})
    
    return chat_history

# Function to handle retrieving session history (from DB instead of a file)
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    return load_session_history(session_id)

# Function to save all sessions (no JSON files)
def save_all_sessions():
    logging.info("No need to save to file. Data is already in the database.")
    # This can be left empty since data is directly stored in the database.

# Example of saving all sessions before exiting the application
import atexit
atexit.register(save_all_sessions)

# Example usage to test insertion
 

# Invoke the chain and save the messages after invocation
 


async def invoke_and_saveS(session_id, input_text):
    # Save the user question with role "human"
    save_message(session_id, "human", input_text)
    full_answer=""
    full_retrieved_data = ""
    
    # Stream the response chunks asynchronously
    async for chunk in conversational_rag_chain.astream(
        {"input": input_text}, config={"configurable": {"session_id": session_id}}
    ):
        # Extract the 'answer' part of the chunk
        answer_chunk = chunk.get('answer', '')
 
        print("=======>",chunk)
         
      

        # Yield each chunk as it is received
        if answer_chunk:
            # print(answer_chunk,'answer')
            yield f"{answer_chunk}\n"
        full_answer += answer_chunk
    # Once streaming is complete, save the AI answer with role "ai"
    # Here, we could also save the entire concatenated result if needed
   
    
    save_message(session_id, "ai", full_answer)

