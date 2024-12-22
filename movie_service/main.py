from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, List
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

# Movie Data (in-memory database)
movies = []

# Movie Model
class Movie(BaseModel):
    id: int
    title: str
    description: str

class MovieCreate(BaseModel):
    title: str
    description: str

# Token verification dependency
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
@app.get("/movies", response_model=List[Movie])
async def get_movies(token: str = Depends(get_token_from_header)):
    return movies

# Create Movie
@app.post("/movies", response_model=Movie)
async def create_movie(movie_data: MovieCreate, token: str = Depends(get_token_from_header)):
    # Generate new ID
    new_id = len(movies) + 1
    movie = Movie(id=new_id, title=movie_data.title, description=movie_data.description)
    movies.append(movie)
    return movie

# Update Movie
@app.put("/movies/{movie_id}", response_model=Movie)
async def update_movie(movie_id: int, movie_data: MovieCreate, token: str = Depends(get_token_from_header)):
    for i, movie in enumerate(movies):
        if movie.id == movie_id:
            updated_movie = Movie(id=movie_id, title=movie_data.title, description=movie_data.description)
            movies[i] = updated_movie
            return updated_movie
    raise HTTPException(status_code=404, detail="Movie not found")

# Delete Movie
@app.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int, token: str = Depends(get_token_from_header)):
    for i, movie in enumerate(movies):
        if movie.id == movie_id:
            del movies[i]
            return {"message": "Movie deleted"}
    raise HTTPException(status_code=404, detail="Movie not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)