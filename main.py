import warnings
import helper as h
import pandas as pd
import streamlit as st
import extra_streamlit_components as stx
import time

spotify = h.SpotifyAPI()
client_id = spotify.client_id
redirect = "https://abdi40party.streamlit.app/?spotify_callback=true"


def get_manager():
    return stx.CookieManager()


def initialize_session_state():
    if 'code' not in st.session_state:
        st.session_state.code = None
    if 'userid' not in st.session_state:
        st.session_state.userid = None
    if 'cookies' not in st.session_state:
        st.session_state['cookies'] = get_manager().get_all()


def handle_spotify_callback():
    query_params = st.query_params
    spotify_callback = query_params.get("spotify_callback", [None])[0]
    if spotify_callback == "true":
        st.session_state.code = query_params.get("code", [None])[0]


def process_token_request():
    if st.session_state.code:
        code_verifier = spotify.get_code_verifier_from_file()
        response_json = spotify.request_access_token(client_id, st.session_state.code, redirect, code_verifier)
        access_token = response_json.get('access_token')
        if access_token:
            st.session_state.access_token = access_token
            userid = spotify.get_current_user_profile(bearer_token=st.session_state.access_token)['id']
            if userid:
                st.session_state.userid = userid
                st.write(f"Hallo {st.session_state.userid}!!")


def request_user_auth():
    if 'code_verifier' not in st.session_state:
        st.session_state.code_verifier = spotify.generate_random_string(128)
    code_verifier = st.session_state.code_verifier
    spotify.save_code_verifier_to_file(code_verifier)
    code_challenge = spotify.generate_code_challenge(code_verifier)
    st.write("Klik hier om je aan te melden bij Spotify:")
    if st.button("Aanmelden"):
        spotify.request_user_authorization(client_id, redirect, code_challenge)


def show_recommendations(bearer_token):
    genres = spotify.get_genres(bearer_token=bearer_token)
    if type(genres) == str:
        st.write(f"Er gaat iets fout, neem contact op met de baas. \n\nFoutmelding: {genres}")
        return
    Name_of_genres = st.multiselect("Genres", genres['genres'], default=genres['genres'][94])
    Name_of_artist = st.text_input("(Optioneel) Vul naam van favo artiest", value="Silk Sonic")
    Danceability = st.slider("Hoe hard wil je dansen (dansbaarheid)?", value=50) / 100
    Energy = st.slider("Hoe hard wil je em voelen (energie)?", value=50) / 100
    Limit = st.slider("Hoeveel liedjes?", min_value=1, max_value=20, value=1)
    if Name_of_artist:
        artist_obj = spotify.search(Name_of_artist)
        artist_id = artist_obj['artists']['items'][0]['id']
    if st.button("OK!"):
        Data = spotify.get_recommendations(bearer_token=bearer_token,
                                           genres=Name_of_genres,
                                           artist=artist_id,
                                           limit=Limit,
                                           target_danceability=Danceability,
                                           target_energy=Energy)
        need = [{
            'Item': i,
            'Artist': item['album']['artists'][0]['name'],
            'Song Name': item['name'],
            'Release Date': item['album']['release_date'],
            'Album Name': item['album']['name'],
            'Id': item['id'],
            'Popularity': item['popularity'],
            'Link': item['external_urls']['spotify'],
            'Image': item['album']['images'][0]['url']
        } for i, item in enumerate(Data['tracks'])]
        Track_df = pd.DataFrame(need)
        st.session_state.Track_df = Track_df
        st.dataframe(
            Track_df,
            column_config={
                "Link": st.column_config.LinkColumn("Song URL"),
                "Image": st.column_config.ImageColumn("Image")
            },
            column_order=("Image", "Artist", "Song Name", "Album Name", "Link", "Popularity"),
            hide_index=True,
        )


def handle_playlists(bearer_token):
    if 'userid' in st.session_state and st.session_state.userid:
        playlists_obj = spotify.get_playlists(bearer_token=bearer_token, user_id=st.session_state.userid)
        playlists = [item['name'] for item in playlists_obj['items']]
        playlist_dict = {item['name']: item['id'] for item in playlists_obj['items']}
        if 'playlist' in st.session_state:
            selected_playlist_name = st.selectbox("Playlist, druk het kruisje rechts om een nieuwe playlist te maken.", list(playlist_dict.keys()), index=st.session_state.playlist, placeholder="Kies een playlist of maak een nieuwe")
        else:
            selected_playlist_name = st.selectbox("Playlist, druk het kruisje rechts om een nieuwe playlist te maken.", list(playlist_dict.keys()), index=None, placeholder="Kies een playlist of maak een nieuwe")
        if not selected_playlist_name:
            handle_new_playlist_creation(playlists)
        else:
            playlist_df = playlist_dict[selected_playlist_name]
            add_tracks_to_playlist(bearer_token, playlist_df)


def handle_new_playlist_creation(playlists):
    Name_of_playlist = st.text_input("Vul de naam van je nieuwe playlist.", placeholder="bijv. Abdi's 40 Party")
    if st.button("Opslaan"):
        check = spotify.check_playlists(Name_of_playlist, playlists)
        if check:
            spotify.create_playlist(bearer_token=st.session_state.access_token,
                                    user_id=st.session_state.userid,
                                    name=Name_of_playlist,
                                    description=Name_of_playlist,
                                    public=True)
            st.session_state.playlist = Name_of_playlist
        else:
            st.write("Playlist bestaat al!")


def add_tracks_to_playlist(bearer_token, playlist_df):
    if 'Track_df' in st.session_state and not st.session_state.Track_df.empty:
        st.caption("Wil je de tracks toevoegen aan je playlist? Klik dan toevoegen.")
        if st.button("Toevoegen"):
            Data_list = st.session_state.Track_df
            track_ids = Data_list['Id'].tolist()
            track_ids_str = ','.join(track_ids)
            added = spotify.add_to_playlist(bearer_token=bearer_token, playlist_id=playlist_df, track_ids=track_ids_str)
            if added:
                st.write("De volgende nummers worden toegevoegd aan jouw playlist: ", Data_list)
                with st.spinner("Nummers worden toegevoegd!"):
                    time.sleep(5)
                st.rerun()


def main():
    warnings.filterwarnings("ignore")
    st.set_page_config(page_title="Abdi's feestje!", page_icon="️‍‍☠️", layout="centered", initial_sidebar_state="auto", menu_items=None)
    st.image("media/somalisonic.png", caption="Somali Sonic")
    st.title("Let's party tonight!!!")

    initialize_session_state()

    # st.session_state['cookies']

    handle_spotify_callback()

    if st.session_state.code:
        process_token_request()
    else:
        request_user_auth()

    if 'access_token' in st.session_state:
        show_recommendations(st.session_state.access_token)
        handle_playlists(st.session_state.access_token)

    with open("ui/styles.md", "r") as styles_file:
        styles_content = styles_file.read()
        
    st.write(styles_content, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
