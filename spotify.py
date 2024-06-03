from dotenv import load_dotenv
import requests
import os
import pandas as pd
import numpy as np

class SpotifyAPI:
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize SpotifyAPI object
        :param client_id: Spotify client id
        :param client_secret: Spotify client secret
        """
        self.api_endpoint = "https://api.spotify.com/v1"
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self.access_token = self.get_access_token([client_id, client_secret])
        if not self.access_token:
            print("Failed to get access token")
            exit(1)

    def get_access_token(self, creds: list[str]) -> str:
        """
        Get access token from Spotify API
        :param creds: list of client_id and client_secret
        :return: access_token
        """
        url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": creds[0],
            "client_secret": creds[1]
        }
        access_token = None
        try:
            res = requests.post(url, headers=self.headers, data=data)
        except requests.exceptions.RequestException as e:
            print("Failed to get token: ", e)
            exit(1)
        else:
            if res.status_code < 400:
                access_token = res.json()['access_token']
                self.headers["Authorization"] = f"Bearer {access_token}"
        return access_token
    
    def get_recommendations(self, seed_tracks: list[str], limit: int = 19):
        """
        Get recommendations based on seed tracks
        :param seed_tracks: list of seed spotify ids (e.g. "6fTt0CH2t0mdeB2N9XFG5r")
        :param limit: number of recommendations to return
        :return: recommendations as a pd.DataFrame object
        """
        url = f"{self.api_endpoint}/recommendations"
        params = {
            "seed_tracks": ",".join(seed_tracks),
            "limit": limit
        }
        try:
            res = requests.get(url, headers=self.headers, params=params)
        except requests.exceptions.RequestException as e:
            print("Failed to get recommendations: ", e)
            exit(1)
        else:
            if res.status_code < 400:
                res = res.json()
                predicted_songs = []
                for track in res['tracks']:
                    track_id = track['external_urls']['spotify'].split('/')[-1]
                    track_features = self.get_track_info(track_id)
                    track = {
                        "id": track_id,
                        "name": track['name'],
                        "artist": track['artists'][0]['name'],
                    }
                    track.update(track_features)
                    predicted_songs.append(track)

                predicted_songs = pd.DataFrame(predicted_songs)
                predicted_songs = predicted_songs.drop(['type', 'uri', 'track_href', 'analysis_url'], axis=1)
                # predicted_songs = predicted_songs.to_numpy()
                return predicted_songs
            else:
                print(res)
                return res.status_code
            
    def get_track_info(self, track_id: str):
        """
        Get track info from Spotify API
        :param track_id: Spotify track id
        :return: track info as a dictionary
        """
        url = f"{self.api_endpoint}/audio-features/{track_id}"
        try:
            res = requests.get(url, headers=self.headers)
        except requests.exceptions.RequestException as e:
            print("Failed to get track info: ", e)
            exit(1)
        else:
            if res.status_code < 400:
                return res.json()

if __name__ == "__main__":
    test_playlists = np.load('misc/test_playlists.npy')
    # print(music_info)
    # print(test_playlists)
    env_path = os.path.join('misc', '.env')
    load_dotenv(dotenv_path=env_path)
    SPOTIFY_CREDS = [os.getenv('SPOTIFY_CLIENT_ID'), 
                    os.getenv('SPOTIFY_CLIENT_SECRET')]

    if not all(SPOTIFY_CREDS):
        print("Please set the SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
        exit(1)

    # track_data = pd.read_csv('misc/music_info.csv')
    # track_data = track_data.drop(['spotify_preview_url'], axis=1)
    # track_data.info()

    spotify = SpotifyAPI(*SPOTIFY_CREDS)
    # print(len(test_playlists))
    # for playlist in test_playlists:
    playlist = test_playlists[0]
    ids = []
    # recommendations = []
    for song in playlist[0:5]:
        song = song.tolist()
        ids.append(song[2])
    #   print(type(song[2]))
    # print(ids)
    # print(len(ids))
    
    recommendations = spotify.get_recommendations(ids)

    # random_tracks = track_data.sample(5)
    # seed_tracks = random_tracks['spotify_id'].tolist()

    # for song in seed_tracks:
    #     print(type(song))
    # print(seed_tracks)
    # print(len(seed_tracks))

    # recommendations = spotify.get_recommendations(seed_tracks)
    print(recommendations)
    recommendations.to_csv('misc/spotify_recs.csv')
    # for song in playlist[0:5]:
    #     print(song[1])
