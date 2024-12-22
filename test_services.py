import requests
import sys
import time
from typing import Optional, Dict, Any
import webbrowser
from urllib.parse import quote, urlencode, urlparse, parse_qs
import json

# Configuration
GATEWAY_URL = "http://localhost:8000"
AUTH_ENDPOINTS = {
    "login": f"{GATEWAY_URL}/login",
    "callback": f"{GATEWAY_URL}/auth/callback",
    "verify": f"{GATEWAY_URL}/verify-token"
}
MOVIES_ENDPOINT = f"{GATEWAY_URL}/movies"

def handle_request_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            print(f"❌ Failed to connect to the server. Is it running?")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {str(e)}")
            return None
    return wrapper

def validate_movie_data(movie: Dict[str, Any]) -> bool:
    required_fields = ['title', 'description']
    return all(field in movie for field in required_fields)

@handle_request_error
def verify_token(token: str) -> bool:
    print("\n=== Verifying Token ===")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(AUTH_ENDPOINTS["verify"], headers=headers)
    return response.status_code == 200

@handle_request_error
def initiate_google_login() -> Optional[str]:
    print("\n=== Initiating Google Login ===")
    response = requests.get(AUTH_ENDPOINTS["login"])
    
    if response.status_code == 200:
        auth_url = response.json().get("authorization_url")
        print("✓ Opening browser for Google authentication...")
        print(f"Authorization URL: {auth_url}")
        webbrowser.open(auth_url)
        
        print("\nAfter logging in with Google, you will be redirected to a URL.")
        print("Copy the ENTIRE redirect URL from your browser and paste it here.")
        callback_url = input("\nPaste the redirect URL here: ").strip()
        
        try:
            parsed_url = urlparse(callback_url)
            params = parse_qs(parsed_url.query)
            return handle_callback(
                params['code'][0],
                params.get('scope', [None])[0],
                params.get('prompt', [None])[0],
                params.get('authuser', [None])[0]
            )
        except (KeyError, IndexError) as e:
            print("❌ Failed to extract authorization code from URL")
            print(f"Error: {str(e)}")
            return None
    else:
        print(f"❌ Failed to initiate login: {response.status_code}")
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")
        return None

@handle_request_error
def handle_callback(auth_code: str, scope: Optional[str] = None, 
                   prompt: Optional[str] = None, authuser: Optional[str] = None) -> Optional[str]:
    print("\n=== Processing Authentication ===")
    
    # Build parameters
    params = {
        'code': auth_code,
        'scope': scope,
        'prompt': prompt,
        'authuser': authuser
    }
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}
    
    try:
        # Wait a bit for the browser callback to complete
        time.sleep(1)
        
        # First attempt to get the token
        response = requests.get(AUTH_ENDPOINTS["callback"], params=params, timeout=30)
        
        if response.status_code == 200:
            token_data = response.json()
            print("✓ Authentication successful!")
            return token_data.get("access_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            try:
                error = response.json()
                if isinstance(error, dict):
                    error = json.dumps(error, indent=2)
                print(f"Error: {error}")
            except:
                print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return None

@handle_request_error
def create_movie(token: str, movie_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    print("\n=== Creating Movie ===")
    if not validate_movie_data(movie_data):
        print("❌ Invalid movie data format")
        return None

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    if 'id' in movie_data:
        del movie_data['id']
        
    response = requests.post(MOVIES_ENDPOINT, json=movie_data, headers=headers)
    
    if response.status_code == 200:
        movie = response.json()
        print(f"✓ Movie created successfully: {movie['title']}")
        return movie
    else:
        print(f"❌ Failed to create movie: {response.status_code}")
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")
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
        print(f"❌ Failed to fetch movies: {response.status_code}")
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")
        return None

@handle_request_error
def update_movie(token: str, movie_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    print(f"\n=== Updating Movie {movie_id} ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    if 'id' in updated_data:
        del updated_data['id']
        
    response = requests.put(f"{MOVIES_ENDPOINT}/{movie_id}", json=updated_data, headers=headers)
    
    if response.status_code == 200:
        movie = response.json()
        print(f"✓ Movie updated successfully: {movie['title']}")
        return movie
    else:
        print(f"❌ Failed to update movie: {response.status_code}")
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")
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
        print(f"❌ Failed to delete movie: {response.status_code}")
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")
        return False

def login() -> Optional[str]:
    """Handle the login process"""
    print("\n=== Login Process ===")
    print("1. Get new access token (Google Login)")
    print("2. Use existing access token")
    choice = input("Choose an option (1/2): ").strip()
    
    if choice == "1":
        token = initiate_google_login()
        if token:
            print("\n✓ Login successful!")
            print(f"\nYour access token: {token}")
            print("\nSave this token for future use!")
        return token
    elif choice == "2":
        token = input("\nEnter your access token: ").strip()
        if verify_token(token):
            print("✓ Token verified successfully!")
            return token
        else:
            print("❌ Invalid or expired token")
            return None
    else:
        print("❌ Invalid choice")
        return None

def test_movie_operations(token: str) -> bool:
    """Test CRUD operations for movies"""
    print("\n=== Starting Movie CRUD Tests ===")

    # Create
    new_movie = {
        "title": "Inception",
        "description": "A mind-bending thriller about dreams within dreams."
    }
    created_movie = create_movie(token, new_movie)
    if not created_movie:
        print("\n❌ Tests failed at movie creation stage")
        return False
    movie_id = created_movie['id']

    # Read
    movies = fetch_movies(token)
    if not movies:
        print("\n❌ Tests failed at movie fetching stage")
        return False

    # Update
    updated_data = {
        "title": "Inception (2010)",
        "description": "A thief who steals corporate secrets through dream-sharing technology."
    }
    updated_movie = update_movie(token, movie_id, updated_data)
    if not updated_movie:
        print("\n❌ Tests failed at movie update stage")
        return False

    # Delete
    if not delete_movie(token, movie_id):
        print("\n❌ Tests failed at movie deletion stage")
        return False

    print("\n✅ All movie operations completed successfully!")
    return True

def run_tests():
    print("=== Movie API Test Suite ===")
    
    # Step 1: Login
    token = login()
    if not token:
        print("\n❌ Tests aborted due to login failure")
        return False
    
    # Step 2: Ask to proceed with tests
    print("\nWould you like to proceed with movie CRUD tests? (y/n)")
    choice = input().strip().lower()
    
    if choice != 'y':
        print("Tests aborted by user")
        return False
    
    # Step 3: Run movie tests
    return test_movie_operations(token)

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