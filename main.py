import warnings, helper as h, pandas as pd, streamlit as st

spotify = h.SpotifyAPI()
bearer_token = spotify.get_access_token(spotify.client_id,spotify.client_secret)

warnings.filterwarnings("ignore")

st.set_page_config(page_title="Abdi's feestje!", page_icon="️‍‍☠️", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.image("/root/spotify/media/somalisonic.png",caption="Somali Sonic")
st.title("Let's party tonight!!!")

genres = spotify.get_genres(bearer_token=bearer_token)

# st.write(genres['genres'])
Name_of_genres = st.multiselect("Genres", genres['genres'],default=genres['genres'][94]) #r-n-b

Name_of_artist = st.text_input("(Optioneel) Vul naam van favo artiest",value="Silk Sonic")
Danceability = st.slider("Hoe hard wil je dansen Abdi?",value=50) / 100
Energy = st.slider("Hoe hard wil je em voelen Abdi?",value=50) / 100
Limit = st.slider("Hoeveel liedjes met deze criteria?",min_value=1,max_value=20,value=1)
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
# st.write(Data)
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
    st.write(Track_df)

    #Create playlist JSON object
    userid = "luciano2001"#spotify.get_current_user_profile(bearer_token=bearer_token)
    playlists_obj = spotify.get_playlists(bearer_token=bearer_token,user_id=userid)
    #Create list of playlist names
    playlists = [item['name'] for item in playlists_obj['items']]
    # Create a dictionary with playlist names as keys and their IDs as values
    playlist_dict = {item['name']: item['id'] for item in playlists_obj['items']}
    # Populate the selectbox with playlist names
    selected_playlist_name = st.selectbox("Playlist", list(playlist_dict.keys()))
    # Fetch the corresponding ID for the selected playlist name
    playlist_df = playlist_dict[selected_playlist_name]

    if not playlist_df:
        Name_of_playlist = st.text_input("Vul de naam van je playlist.",value="bijv. Abdi's 40 Party")
        button_store_playlist = st.button("Opslaan")

        if button_store_playlist:
            check = spotify.check_playlists(Name_of_playlist,playlists)
            if not check:
                spotify.create_playlist(bearer_token=bearer_token,
                                        user_id=userid,
                                        name=Name_of_playlist,
                                        description=Name_of_playlist,
                                        public=True)
            else:
                st.write("Playlist bestaat al!")

    if not Track_df.empty and playlist_df:
        st.caption("Wil je de tracks toevoegen aan je playlist? Klik dan toevoegen.")
        button_add_playlist = st.button("Toevoegen")
        if button_add_playlist:
            print(button_add_playlist)
            track_ids = [item['id'] for item in Data['tracks']]
            track_ids_str = ','.join(track_ids)
            added = spotify.add_to_playlist(bearer_token=bearer_token,playlist_id=playlist_df,track_ids=track_ids_str)
        


with open("ui/styles.md", "r") as styles_file:
    styles_content = styles_file.read()

st.write(styles_content, unsafe_allow_html=True)