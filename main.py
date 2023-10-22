import warnings, helper as h, pandas as pd, streamlit as st, time

spotify = h.SpotifyAPI()
# bearer_token = spotify.get_access_token(spotify.client_id,spotify.client_secret)
client_id = spotify.client_id
redirect = "https://abdi40party.streamlit.app/?spotify_callback=true"

# Streamlit App
def main():
    warnings.filterwarnings("ignore")

    st.set_page_config(page_title="Abdi's feestje!", page_icon="️‍‍☠️", layout="centered", initial_sidebar_state="auto", menu_items=None)
    st.image("media/somalisonic.png",caption="Somali Sonic")
    st.title("Let's party tonight!!!")

    if 'code' not in st.session_state:
        st.session_state.code = None    

    # Check if we're in the Spotify callback
    query_params = st.experimental_get_query_params()
    spotify_callback = query_params.get("spotify_callback", [None])[0]
    if spotify_callback == "true":
        # We're in the callback, capture the code
        st.session_state.code = query_params.get("code", [None])[0]

    # If we have the code, proceed with the token request
    if st.session_state.code:
        # Step 3: Request Access Token
        code_verifier = spotify.get_code_verifier_from_file()
        response_json = spotify.request_access_token(client_id, st.session_state.code, redirect, code_verifier)
        access_token = response_json.get('access_token')
        if access_token is not None:
            st.session_state.access_token = access_token
        userid = spotify.get_current_user_profile(bearer_token=st.session_state.access_token)['id']
        if userid:
            st.session_state.userid = userid
            st.write("Hallo ",st.session_state.userid,"!!")

    else:
        # Step 1: Generate Code Verifier and Challenge
        if 'code_verifier' not in st.session_state:
            st.session_state.code_verifier = spotify.generate_random_string(128)         
        code_verifier = st.session_state.code_verifier
        spotify.save_code_verifier_to_file(code_verifier)
        code_challenge = spotify.generate_code_challenge(code_verifier)

        st.write("Klik hier om je aan te melden bij Spotify:")
        if st.button("Aanmelden"):
            spotify.request_user_authorization(client_id, redirect, code_challenge)

    if 'access_token' in st.session_state:
        bearer_token = st.session_state.access_token
        genres = spotify.get_genres(bearer_token=bearer_token)
        if type(genres) == str:
            st.write("Er gaat iets fout, neem contact op met de baas. \n\nFoutmelding:" ,genres)
            return
        Name_of_genres = st.multiselect("Genres", genres['genres'],default=genres['genres'][94])
        Name_of_artist = st.text_input("(Optioneel) Vul naam van favo artiest",value="Silk Sonic")
        Danceability = st.slider("Hoe hard wil je dansen (dansbaarheid)?",value=50) / 100
        Energy = st.slider("Hoe hard wil je em voelen (energie)?",value=50) / 100
        Limit = st.slider("Hoeveel liedjes?",min_value=1,max_value=20,value=1)
        button_clicked = st.button("OK!")

        if Name_of_artist:
            artist_obj = spotify.search(Name_of_artist)
            artist_id = artist_obj['artists']['items'][0]['id']

        if button_clicked: 
            Data = spotify.get_recommendations(bearer_token=bearer_token,
                                            genres=Name_of_genres,
                                            artist=artist_id,
                                            limit=Limit,
                                            target_danceability=Danceability,
                                            target_energy=Energy)

            st.write(Data)
            need = []
            for i, item in enumerate(Data['tracks']):
                track = item['album']
                track_id = item['id']
                song_name = item['name']
                popularity = item['popularity']
                need.append({
                    'Item': i, 
                    'Artist': track['artists'][0]['name'], 
                    'Song Name': song_name, 
                    'Release Date': track['release_date'],
                    'Album Name': track['name'], 
                    'Id': track_id,  
                    'Popularity': popularity
                })
            Track_df = pd.DataFrame(need)
            st.session_state.Track_df = Track_df
            st.write(Track_df)


        #Create playlist JSON object
        playlists_obj = spotify.get_playlists(bearer_token=bearer_token,user_id=st.session_state.userid)
        #Create list of playlist names
        playlists = [item['name'] for item in playlists_obj['items']]
        # Create a dictionary with playlist names as keys and their IDs as values
        playlist_dict = {item['name']: item['id'] for item in playlists_obj['items']}
        # Populate the selectbox with playlist names
        if 'playlist' in st.session_state:
            selected_playlist_name = st.selectbox("Playlist, druk het kruisje rechts om een nieuwe playlist te maken.", list(playlist_dict.keys()),index=st.session_state.playlist,placeholder="Kies een playlist of maak een nieuwe")
        else:
            selected_playlist_name = st.selectbox("Playlist, druk het kruisje rechts om een nieuwe playlist te maken.", list(playlist_dict.keys()),index=None,placeholder="Kies een playlist of maak een nieuwe")
        # Fetch the corresponding ID for the selected playlist name
        if not selected_playlist_name:
            Name_of_playlist = st.text_input("Vul de naam van je nieuwe playlist.",placeholder="bijv. Abdi's 40 Party")
            button_store_playlist = st.button("Opslaan")
            playlist_df = None
            if button_store_playlist:
                check = spotify.check_playlists(Name_of_playlist,playlists)
                if check:
                    spotify.create_playlist(bearer_token=bearer_token,
                                            user_id=userid,
                                            name=Name_of_playlist,
                                            description=Name_of_playlist,
                                            public=True)
                    st.session_state.playlist = Name_of_playlist
                else:
                    st.write("Playlist bestaat al!")
        else:
            playlist_df = playlist_dict[selected_playlist_name]

        if 'Track_df' in st.session_state and not st.session_state.Track_df.empty and playlist_df:
            st.caption("Wil je de tracks toevoegen aan je playlist? Klik dan toevoegen.")
            
            st.session_state.button_clicked = False
            button_add_playlist = st.button("Toevoegen")

            if button_add_playlist:
                st.session_state.button_clicked = True

            if st.session_state.button_clicked:
                Data_list = st.session_state.Track_df
                track_ids = Data_list['Id'].tolist()
                track_ids_str = ','.join(track_ids)
                added = spotify.add_to_playlist(bearer_token=bearer_token,playlist_id=playlist_df,track_ids=track_ids_str)
                if added:
                    st.write("De volgende nummers worden toegevoegd aan jouw playlist: ", Data_list)
                    with st.spinner("Nummers worden toegevoegd!"):
                        time.sleep(5)
                    st.rerun()

        with open("ui/styles.md", "r") as styles_file:
            styles_content = styles_file.read()

        st.write(styles_content, unsafe_allow_html=True)

if __name__ == "__main__":
    main()