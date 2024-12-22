from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from typing import Optional
import json
import logging
from urllib.parse import quote, unquote
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
TOKEN_URL = os.getenv('TOKEN_URL')
USER_INFO_URL = os.getenv('USER_INFO_URL')
GOOGLE_AUTH_URL = os.getenv('GOOGLE_AUTH_URL')

# FastAPI App
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

class UserInfo(BaseModel):
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None

@app.get("/login")
async def initiate_login():
    scope = "email profile openid"
    auth_url = (
        f"{GOOGLE_AUTH_URL}"
        f"?response_type=code"
        f"&client_id={quote(CLIENT_ID)}"
        f"&redirect_uri={quote(REDIRECT_URI)}"
        f"&scope={quote(scope)}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    logger.info(f"Generated auth URL: {auth_url}")
    return {"authorization_url": auth_url}

@app.get("/auth/callback")
async def auth_callback(
    request: Request,
    code: str,
    scope: Optional[str] = None,
    authuser: Optional[str] = None,
    prompt: Optional[str] = None
):
    """Handle the OAuth2 callback from Google"""
    try:
        logger.info("Starting token exchange...")
        logger.debug(f"Received code: {code[:10]}...")
        logger.debug(f"Full query params: {request.query_params}")  # Debug log

        token_data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI
        }

        # Log the token request data (excluding secret)
        logger.debug(f"Token request data: {token_data}")

        # Make token exchange request
        token_response = requests.post(
            TOKEN_URL,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30
        )

        logger.debug(f"Token response status: {token_response.status_code}")
        logger.debug(f"Token response body: {token_response.text}")

        if token_response.status_code != 200:
            error_text = token_response.text
            logger.error(f"Token exchange failed. Response: {error_text}")
            raise HTTPException(
                status_code=token_response.status_code,
                detail=error_text
            )

        token_json = token_response.json()
        access_token = token_json.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token in response")

        # Get user info
        user_response = requests.get(
            USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=user_response.status_code,
                detail=f"Failed to get user info: {user_response.text}"
            )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_info": user_response.json()
        }

    except HTTPException as he:
        logger.error(f"HTTP Exception: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/verify-token")
async def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
        user_response = requests.get(
            USER_INFO_URL,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )

        if user_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return user_response.json()
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="debug")