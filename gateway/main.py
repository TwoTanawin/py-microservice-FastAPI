from fastapi import FastAPI, HTTPException, Request
import httpx
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

# FastAPI App
app = FastAPI()

# Token cache
token_cache: Dict[str, dict] = {}

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
LOGIN_SERVICE_URL = "http://localhost:8001"
MOVIE_SERVICE_URL = "http://localhost:8002"

@app.get("/login")
async def login():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{LOGIN_SERVICE_URL}/login")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle OAuth callback and cache the token"""
    async with httpx.AsyncClient() as client:
        try:
            # Get the code from query params
            code = request.query_params.get('code')
            
            # If we have the token cached, return it
            if code and code in token_cache:
                return token_cache[code]
            
            # Forward the request to login service
            query_string = str(request.url.query)
            response = await client.get(
                f"{LOGIN_SERVICE_URL}/auth/callback?{query_string}",
                timeout=30.0
            )
            
            if response.status_code == 200:
                token_data = response.json()
                # Cache the token
                if code:
                    token_cache[code] = token_data
                return token_data
            
            # Handle errors
            try:
                error_detail = response.json()
            except:
                error_detail = response.text
            raise HTTPException(status_code=response.status_code, detail=error_detail)
            
        except httpx.RequestError as exc:
            raise HTTPException(status_code=500, detail=str(exc))

@app.get("/get-cached-token/{code}")
async def get_cached_token(code: str):
    """Retrieve cached token for a given authorization code"""
    if code in token_cache:
        return token_cache.pop(code)  # Remove after use
    raise HTTPException(status_code=404, detail="Token not found")

@app.get("/verify-token")
async def verify_token(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{LOGIN_SERVICE_URL}/verify-token",
            headers={"Authorization": token}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.get("/movies")
async def get_movies(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MOVIE_SERVICE_URL}/movies",
            headers={"Authorization": token}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.post("/movies")
async def create_movie(request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MOVIE_SERVICE_URL}/movies",
            headers={"Authorization": token},
            json=body
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.put("/movies/{movie_id}")
async def update_movie(movie_id: int, request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    body = await request.json()
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{MOVIE_SERVICE_URL}/movies/{movie_id}",
            headers={"Authorization": token},
            json=body
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

@app.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int, request: Request):
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="No authorization header")
    
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{MOVIE_SERVICE_URL}/movies/{movie_id}",
            headers={"Authorization": token}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)