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
    
    def get_recommendations(self, seed_tracks: list[str] = "", features: dict = {}, limit: int = 10):
        """
        Get recommendations based on seed tracks
        :param seed_tracks: list of seed spotify ids (e.g. "6fTt0CH2t0mdeB2N9XFG5r")
        :param limit: number of recommendations to return
        :return: recommendations as a pd.DataFrame object
        """
        url = f"{self.api_endpoint}/recommendations"
        params = {
            "seed_tracks": ",".join(seed_tracks) if seed_tracks else None,
            "limit": limit
        }
        params = {**params, **features}
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
                print(res.text)
                return res
            
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
