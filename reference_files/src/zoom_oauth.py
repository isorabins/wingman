from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from httpx import AsyncClient
from src.config import Config

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Zoom API credentials
ZOOM_ACCOUNT_ID = Config.ZOOM_ACCOUNT_ID
ZOOM_CLIENT_ID = Config.ZOOM_CLIENT_ID
ZOOM_CLIENT_SECRET = Config.ZOOM_CLIENT_SECRET

# Zoom API endpoints
ZOOM_TOKEN_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE_URL = Config.ZOOM_API_URL

# In-memory storage for the access token (use secure storage in production)
access_token = None

async def get_access_token():
    global access_token
    if access_token is None:
        try:
            async with AsyncClient() as client:
                print(f"ZOOM_TOKEN_URL: {ZOOM_TOKEN_URL}")
                print(f"ZOOM_ACCOUNT_ID: {ZOOM_ACCOUNT_ID}")
                print(f"ZOOM_CLIENT_ID: {ZOOM_CLIENT_ID}")
                print(f"ZOOM_CLIENT_SECRET: {ZOOM_CLIENT_SECRET[:5]}...")  # Print only first 5 chars for security
                
                response = await client.post(
                    ZOOM_TOKEN_URL,
                    params={
                        "grant_type": "account_credentials",
                        "account_id": ZOOM_ACCOUNT_ID,
                    },
                    auth=(ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET),
                )
                print(f"Response status: {response.status_code}")
                print(f"Response content: {response.content}")
                response.raise_for_status()
                token_data = response.json()
                access_token = token_data["access_token"]
        except Exception as e:
            print(f"Exception details: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get access token: {str(e)}")
    return access_token

async def make_zoom_request(endpoint, method="GET", data=None):
    token = await get_access_token()
    url = f"{ZOOM_API_BASE_URL}/{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=response.status_code, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to the Fridays at Four Zoom Integration API"}

@app.get("/zoom/user")
async def get_user_info():
    """Get information about the authenticated user"""
    return await make_zoom_request("users/me")

@app.get("/zoom/meetings")
async def list_meetings():
    """List the user's meetings"""
    return await make_zoom_request("users/me/meetings")

@app.get("/zoom/recordings")
async def list_recordings():
    """List the user's cloud recordings"""
    return await make_zoom_request("users/me/recordings")

@app.get("/zoom/meeting/{meeting_id}")
async def get_meeting_details(meeting_id: str):
    """Get details of a specific meeting"""
    return await make_zoom_request(f"meetings/{meeting_id}")

@app.get("/zoom/recording/{meeting_id}")
async def get_meeting_recording(meeting_id: str):
    """Get recording information for a specific meeting"""
    return await make_zoom_request(f"meetings/{meeting_id}/recordings")

@app.get("/zoom/transcript/{meeting_id}")
async def get_meeting_transcript(meeting_id: str):
    """Get transcript for a specific meeting"""
    recordings = await make_zoom_request(f"meetings/{meeting_id}/recordings")
    for file in recordings.get("recording_files", []):
        if file["file_type"] == "TRANSCRIPT":
            return {"transcript_url": file["download_url"]}
    return {"message": "No transcript found for this meeting"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)