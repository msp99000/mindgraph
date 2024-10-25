from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import logging
from rag.ragMainSimple import invoke_and_saveS  # Ensure this import is correct
import uvicorn
import httpx
from dotenv import load_dotenv
import os
from slack.fetch_conversation import slack_fetch_chat
from rag.embeddingdb import create_vector_store
from pydantic import BaseModel
from typing import Optional, Dict
from sql_connect.main import fetch_session_history,create_table_if_not_exists_and_insert_initial_user
from passlib.context import CryptContext
import psycopg2
from fastapi.responses import StreamingResponse
# Initialize the FastAPI app
app = FastAPI()
db_params = {
    'host': 'db',
    'database': "slackpoc",
    'user': 'postgres',
    'password': 'postgres'
}
# Enable CORS for all domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains, change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
fake_users_db: Dict[str, str] = {}
create_table_if_not_exists_and_insert_initial_user('upcoretech', 'Upcore@12345')

class User(BaseModel):
    username: str
    password: str

class SessionData(BaseModel):
    sessionID: str

@app.post("/llm_response/{message}")
async def llm_response(message: str, session_data: SessionData):
    try:
        # Create an async generator to stream chunks of the response
        async def event_stream():
            async for result in invoke_and_saveS(session_data.sessionID, message):
                yield f"{result}"  # Use Server-Sent Events format for streaming
                
        # Return the StreamingResponse for real-time streaming
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    
    except Exception as e:
        logging.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
class Sessionid(BaseModel):
    sessionID: Optional[str] = None

@app.post("/api/session")
async def session_data(session: Sessionid):
    try:
        session_fetch = fetch_session_history(session.sessionID)
        
        if not session_fetch:  # Check if session_fetch is empty or None
            raise HTTPException(status_code=404, detail="No session data found for the provided session ID")
        
        return session_fetch  # Return the fetched session history if data is present
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

SLACK_API_org = 'https://slack.com/api/team.info'
SLACK_API_Channel = 'https://slack.com/api/conversations.list?types=public_channel,private_channel&exclude_archived=true'

class TokenRequest(BaseModel):
    token: str

@app.post("/api/slack/combined-info")
async def get_combined_info(token_request: TokenRequest):
    token = token_request.token

    try:
        async with httpx.AsyncClient() as client:
            # Fetch team info
            team_response = await client.get(SLACK_API_org, headers={
                'Authorization': f'Bearer {token}',
            })
            team_response.raise_for_status()

            # Fetch channels info
            channels_response = await client.get(SLACK_API_Channel, headers={
                'Authorization': f'Bearer {token}',
            })
            channels_response.raise_for_status()

            # Return both responses
            return {
                "team_info": team_response.json(),
                "channels_info": channels_response.json()
            }
    except httpx.HTTPStatusError as http_error:
        logging.error(f"HTTP error occurred: {http_error}", exc_info=True)
        raise HTTPException(status_code=http_error.response.status_code, detail="Failed to fetch data")
    except Exception as e:
        logging.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")

class EmbeddingRequest(BaseModel):
    organization_id: str
    organization_name: str
    channel_name: str
    channel_id: str
    latest_unix: Optional[int] = None  # Optional fields
    oldest_unix: Optional[int] = None
    token: str

@app.post("/api/slack/embedding-data")
async def embedding_data(embedding_data: EmbeddingRequest):
    try:
        # Log the incoming request
        logging.info("Received embedding data request")
        
        # Extract data from the request body
        organization_id = embedding_data.organization_id
        organization_name = embedding_data.organization_name
        channel_name = embedding_data.channel_name
        channel_id = embedding_data.channel_id
        latest_unix = embedding_data.latest_unix
        oldest_unix = embedding_data.oldest_unix
        token = embedding_data.token
        
        logging.info(f"Processing request for channel: {channel_id}")

        if latest_unix is None and oldest_unix is None and channel_id:
            logging.info(f"Fetching chat for channel: {channel_id}")
            # Call your Slack fetch chat function (pass appropriate params)
            await slack_fetch_chat(token, channel_id, organization_name, limit=1000)
            return {"success": True, "message": "Data fetched successfully"}
        
        elif channel_id and latest_unix and oldest_unix:
            logging.info(f"Fetching chat from {oldest_unix} to {latest_unix} for channel: {channel_id}")
            # Call your Slack fetch chat function with unix timestamps
            await slack_fetch_chat(token, channel_id, organization_name, oldest_unix=oldest_unix, latest_unix=latest_unix, limit=1000)
            return {"success": True, "message": "Data fetched successfully for the specified time range"}
        
        else:
            raise HTTPException(status_code=400, detail="channel_id or both latest_unix and oldest_unix must be provided.")

    except Exception as e:
        logging.error(f"Error occurred: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/slack/store-vector")
async def store_vector():
    try:
        print("Starting store_vector API endpoint")
        db, message = await create_vector_store()
        if db is not None:
            print("Vector store created or updated successfully")
            return {"message": message, "db":db,"success": True}
        else:
            print(f"Failed to create or update vector store: {message}")
            return {"error": message}
    except Exception as e:
        print(f"Error in store_vector API: {str(e)}")
        return {"error": f"Error occurred: {str(e)}"}

@app.post("/api/login")
async def login(user: User):
    """Log in a user."""
    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cursor:
            # Fetch the hashed password from the database
            cursor.execute("SELECT hashed_password FROM users WHERE username = %s", (user.username,))
            result = cursor.fetchone()
            
            if result is None:
                # If no user is found with the provided username
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            hashed_password = result[0]
            # Verify the provided password against the stored hashed password
            if pwd_context.verify(user.password, hashed_password):
                return {"message": "Login successful", "username": user.username}
            else:
                # If the password does not match
                raise HTTPException(status_code=401, detail="Invalid username or password")
    except HTTPException as e:
        logging.error(f"Login error - status: {e.status_code}, detail: {e.detail}")
        raise e
    except Exception as e:
        logging.error(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
    # finally:
    #     if conn:
    #         conn.close()



@app.post("/api/register")
async def register(user: User):
    """Register a new user."""
    hashed_password = pwd_context.hash(user.password)
    try:
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cursor:
            # Insert the new user into the database
            cursor.execute("INSERT INTO users (username, hashed_password) VALUES (%s, %s)", 
                           (user.username, hashed_password))
            conn.commit()
        return {"message": "User registered successfully."}
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists.")
    except Exception as e:
        logging.error(f"Error during registration: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Run the FastAPI app using Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)  # Set debug=False in production
