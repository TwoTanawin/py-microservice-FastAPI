from fastapi import FastAPI, HTTPException, Request, Form
import httpx
from fastapi.middleware.cors import CORSMiddleware

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

# Service URLs
LOGIN_SERVICE_URL = "http://localhost:8001"
MOVIE_SERVICE_URL = "http://localhost:8002"

# Login Endpoint
@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    async with httpx.AsyncClient() as client:
        form_data = {
            "username": username,
            "password": password
        }
        response = await client.post(f"{LOGIN_SERVICE_URL}/login", data=form_data)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()

# Get Movies
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
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()

# Create Movie
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
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()

# Update Movie
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
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()

# Delete Movie
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
        raise HTTPException(status_code=response.status_code, detail=response.json())
    return response.json()