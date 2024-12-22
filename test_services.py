import requests
import sys
import time
from typing import Optional, Dict, Any

# Configuration
GATEWAY_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{GATEWAY_URL}/login"
MOVIES_ENDPOINT = f"{GATEWAY_URL}/movies"

# Test Credentials
TEST_EMAIL = "test@test.com"
TEST_PASSWORD = "11111111"

def handle_request_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            print(f"Failed to connect to the server. Is it running?")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return None
    return wrapper

def validate_movie_data(movie: Dict[str, Any]) -> bool:
    required_fields = ['id', 'title', 'description']
    return all(field in movie for field in required_fields)

@handle_request_error
def login() -> Optional[str]:
    print("\n=== Testing Login ===")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(
        LOGIN_ENDPOINT,
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
        headers=headers
    )
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print("✓ Login successful! Token received.")
        return token
    else:
        print(f"✗ Login failed: {response.status_code}")
        print(f"Error: {response.json()}")
        return None

@handle_request_error
def create_movie(token: str, movie_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    print("\n=== Creating Movie ===")
    if not validate_movie_data(movie_data):
        print("✗ Invalid movie data format")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(MOVIES_ENDPOINT, json=movie_data, headers=headers)
    
    if response.status_code == 200:
        movie = response.json()
        print(f"✓ Movie created successfully: {movie['title']}")
        return movie
    else:
        print(f"✗ Failed to create movie: {response.status_code}")
        print(f"Error: {response.json()}")
        return None

@handle_request_error
def fetch_movies(token: str) -> Optional[list]:
    print("\n=== Fetching Movies ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(MOVIES_ENDPOINT, headers=headers)
    
    if response.status_code == 200:
        movies = response.json()
        print(f"✓ Retrieved {len(movies)} movies successfully")
        return movies
    else:
        print(f"✗ Failed to fetch movies: {response.status_code}")
        print(f"Error: {response.json()}")
        return None

@handle_request_error
def update_movie(token: str, movie_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    print(f"\n=== Updating Movie {movie_id} ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.put(f"{MOVIES_ENDPOINT}/{movie_id}", json=updated_data, headers=headers)
    
    if response.status_code == 200:
        movie = response.json()
        print(f"✓ Movie updated successfully: {movie['title']}")
        return movie
    else:
        print(f"✗ Failed to update movie: {response.status_code}")
        print(f"Error: {response.json()}")
        return None

@handle_request_error
def delete_movie(token: str, movie_id: int) -> bool:
    print(f"\n=== Deleting Movie {movie_id} ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(f"{MOVIES_ENDPOINT}/{movie_id}", headers=headers)
    
    if response.status_code == 200:
        print("✓ Movie deleted successfully")
        return True
    else:
        print(f"✗ Failed to delete movie: {response.status_code}")
        print(f"Error: {response.json()}")
        return False

def run_tests():
    print("Starting API Tests...")
    
    # Step 1: Login
    token = login()
    if not token:
        print("\n❌ Tests failed at login stage")
        return False

    # Step 2: Create a Movie
    new_movie = {
        "id": 1,
        "title": "Inception",
        "description": "A mind-bending thriller about dreams within dreams."
    }
    created_movie = create_movie(token, new_movie)
    if not created_movie:
        print("\n❌ Tests failed at movie creation stage")
        return False

    # Step 3: Fetch Movies
    movies = fetch_movies(token)
    if not movies:
        print("\n❌ Tests failed at movie fetching stage")
        return False

    # Step 4: Update Movie
    updated_data = {
        "id": 1,
        "title": "Inception (2010)",
        "description": "A thief who steals corporate secrets through dream-sharing technology."
    }
    updated_movie = update_movie(token, 1, updated_data)
    if not updated_movie:
        print("\n❌ Tests failed at movie update stage")
        return False

    # Step 5: Delete Movie
    if not delete_movie(token, 1):
        print("\n❌ Tests failed at movie deletion stage")
        return False

    print("\n✅ All tests completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error occurred: {str(e)}")
        sys.exit(1)