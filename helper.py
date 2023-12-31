import  webbrowser, hashlib, random, string, base64, requests, datetime, pandas as pd,json as js, streamlit as st
from streamlit.components.v1 import html
from urllib.parse import urlencode

spotify_client_id = st.secrets['CLIENT_ID']
spotify_client_secret = st.secrets['CLIENT_SECRET']

class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = spotify_client_id
    client_secret = spotify_client_secret
    token_url = "https://accounts.spotify.com/api/token"

    def open_page(self,url):
        open_script= """
            <script type="text/javascript">
                window.open('%s', '_blank').focus();
            </script>
        """ % (url)
        html(open_script)

    def get_resource_header(self):
        access_token = self.get_access_token(spotify_client_id=spotify_client_id, spotify_client_secret=spotify_client_secret)
        headers = {
            "Authorization": f"Bearer {access_token}"
        }      
        return headers

    def get_access_token(self,spotify_client_id: str, spotify_client_secret: str) -> str:
        spotify_url = "https://accounts.spotify.com/api/token"
        auth_header = base64.b64encode(f"{spotify_client_id}:{spotify_client_secret}".encode()).decode()

        headers = {
            'Authorization': f'Basic {auth_header}'
        }

        data = {
            'grant_type': 'client_credentials'
        }

        response = requests.post(spotify_url, headers=headers, data=data)

        if response.status_code == 200:
            token = response.json().get('access_token')
        return token

    def get_artist_info(self,artist_id:str, bearer_token:str) -> object:
        endpoint = "https://api.spotify.com/v1/artists/"
        artist_uri = endpoint + artist_id
        headers = {
            'Authorization': f'Bearer  {bearer_token}'
        }
        response = requests.get(artist_uri, headers=headers)
        if response.status_code == 200:
            json = response.json()
        return json


    def get_categories(self,bearer_token:str) -> object:
        endpoint = "https://api.spotify.com/v1/browse/categories?limit=50"
        headers = {
            'Authorization': f'Bearer  {bearer_token}'
        }
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            json = response.json()
        return json


    def get_genres(self,bearer_token:str) -> object:
        endpoint = "https://api.spotify.com/v1/recommendations/available-genre-seeds"
        headers = {
            'Authorization': f'Bearer  {bearer_token}'
        }
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 429:
            returnmsg = f"rate limited with status code: {response.status_code}, try again in: {response.headers.get('Retry-After')} seconds."
            return returnmsg
        if response.status_code == 200:
            json = response.json()
        return json

    def base_search(self, query_params):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200, 299):
            return {}  
        return r.json()

    def search(self, query=None, operator=None, operator_query=None, search_type='artist'):
        if query == None:
            raise Exception("A query is required")
        if isinstance(query, dict):
            query = " ".join([f"{k}:{v}" for k,v in query.items()])
        if operator != None and operator_query != None:
            if operator.lower() == "or" or operator == "not":
                operator = operator.upper()
                if isinstance(operator_query, str):
                    query = f"{query} {operator} {operator_query}"
        query_params = urlencode({"q": query,"type": search_type.lower()})
        return self.base_search(query_params)

    def search_genres(self,genres, bearer_token:str, types="artist,track", limit=20):
        base_url = "https://api.spotify.com/v1/search"
        # Format the genres for the query
        query = "+".join([f"genre%3A{genre}" for genre in genres])
        headers = {
            'Authorization': f'Bearer  {bearer_token}'
        }
        params = {
            "q": query,
            "type": types,
            "limit": limit
        }
        response = requests.get(base_url, headers=headers, params=params)
        return response.json()

    def get_recommendations(self,bearer_token:str,genres,artist=None, track=None,limit=20,market="NL",target_danceability=0.8,target_energy=0.5):
        endpoint = "https://api.spotify.com/v1/recommendations"
        if isinstance(genres, dict):
            genres = " ".join([f"{i}:{genre}" for i, genre in enumerate(genres)])
        # artist = 
        # track = 
        headers = {
            'Authorization': f'Bearer  {bearer_token}'
        }
        params = {
            "seed_genres": ",".join(genres),
            "seed_artists": artist,
            # "seed_tracks": ",".join(track),
            "market": market,
            "limit": limit,
            "target_danceability": target_danceability,
            "target_energy": target_energy
        }
        # print(params)
        params = {k: v for k, v in params.items() if v is not None}
        params = urlencode(params)
        # Filter out None values
        r = requests.get(endpoint, headers=headers, params=params)
        if r.status_code not in range(200, 299):
            return {}  
        return r.json()

    def get_playlists(self,bearer_token:str,user_id:str) -> object:
        endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        headers = {
            'Authorization': f'Bearer  {bearer_token}'
        }
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            json = response.json()
        return json

    def check_playlists(self,playlist_name, playlists):
        """Checks if playlist has not been created yet."""
        return playlist_name not in playlists

    def save_playlists(self,playlist, playlist_name, playlists_df):
        """Saves playlist in a csv file."""
        new_playlist = {
            'name':playlist_name,
            'id':playlist['id'],
            'link':playlist['external_urls']['spotify']
        }

        playlists_df = pd.concat([playlists_df, pd.DataFrame([new_playlist])])
        playlists_df.to_csv("playlists.csv", index=False)

    def get_current_user_profile(self,bearer_token: str) -> object:
        endpoint = "https://api.spotify.com/v1/me"
        headers = {
            'Authorization': f'Bearer {bearer_token}'
        }
        response = requests.get(endpoint, headers=headers)
        if response.status_code == 200:
            json = response.json()
            return json
        if response.status_code != 200:
        # Handle error
            print(f"Error getting user profile: {response.text}")
            return None  # or return an appropriate error message or value
    
    def create_playlist(self,bearer_token:str,user_id:str,name:str,description:str,public:bool) -> object:
        endpoint = f"https://api.spotify.com/v1/users/{user_id}/playlists"
        headers = {
            'Authorization': f'Bearer {bearer_token}',
            'Content-Type': 'application/json',
        }
        data = {
            "name": name,
            "description": description,
            "public": public
        }
        response = requests.post(endpoint, headers=headers, data=js.dumps(data))
        if response.status_code == 201:
            json = response.json()
        return json        
    
    def add_to_playlist(self,bearer_token:str,playlist_id:str,track_ids:str) -> bool:
        endpoint = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
        headers = {
            'Authorization': f'Bearer  {bearer_token}',
            'Content-Type': 'application/json',
        }

        # Convert comma-separated track IDs to a list of track URIs
        uris = [f"spotify:track:{track_id}" for track_id in track_ids.split(",")]

        # Create the payload
        data = {
            "uris": uris,
            "position": 0
        }
        # Send the POST request
        response = requests.post(endpoint, headers=headers, data=js.dumps(data))
        print(response.text)
        # Return True if the request was successful, otherwise return False
        r = False
        if response.status_code == 201:
            r = True
        return r   
    
    def generate_random_string(self,length):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for i in range(length))
    
    def generate_code_challenge(self,code_verifier):
        sha256 = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        base64_url = base64.urlsafe_b64encode(sha256).rstrip(b'=')
        return base64_url.decode('utf-8')
    
    def request_user_authorization(self,client_id, redirect_uri, code_challenge):
        state = self.generate_random_string(16)
        scope = 'user-read-private user-read-email playlist-modify-public playlist-modify-private'
        auth_url = (f"https://accounts.spotify.com/authorize?response_type=code&client_id={client_id}"
                    f"&scope={scope}&redirect_uri={redirect_uri}&state={state}"
                    f"&code_challenge_method=S256&code_challenge={code_challenge}")
        st.button('Open link', on_click=self.open_page(auth_url))

    def request_access_token(self,client_id, code, redirect_uri, code_verifier):
        token_url = "https://accounts.spotify.com/api/token"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'code_verifier': code_verifier
        }
        response = requests.post(token_url, headers=headers, data=data)
        return response.json()

    def save_code_verifier_to_file(self,code_verifier):
        with open('code_verifier.txt', 'w') as f:
            f.write(code_verifier)

    def get_code_verifier_from_file(self):
        with open('code_verifier.txt', 'r') as f:
            return f.read().strip()

