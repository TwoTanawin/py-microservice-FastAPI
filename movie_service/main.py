from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
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

# Movie Data
movies = []

# Movie Model
class Movie(BaseModel):
    id: int
    title: str
    description: str

async def get_token_from_header(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        return token
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

# Get Movies
@app.get("/movies")
async def get_movies(token: str = Depends(get_token_from_header)):
    return movies

# Create Movie
@app.post("/movies")
async def create_movie(movie: Movie, token: str = Depends(get_token_from_header)):
    movies.append(movie)
    return movie

# Update Movie
@app.put("/movies/{movie_id}")
async def update_movie(movie_id: int, movie: Movie, token: str = Depends(get_token_from_header)):
    for i, m in enumerate(movies):
        if m.id == movie_id:
            movies[i] = movie
            return movie
    raise HTTPException(status_code=404, detail="Movie not found")

# Delete Movie
@app.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int, token: str = Depends(get_token_from_header)):
    for i, m in enumerate(movies):
        if m.id == movie_id:
            del movies[i]
            return {"message": "Movie deleted"}
    raise HTTPException(status_code=404, detail="Movie not found")