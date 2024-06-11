import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import random 
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Load the data
file_path = 'misc/data/new_music_info_with_embeddings.csv'
data = pd.read_csv(file_path)

original_data = pd.read_csv('misc/data/processed_music_info.csv')


data['embedding'] = data['embedding'].apply(eval)


embeddings = np.array(data['embedding'].tolist())


additional_extra = pd.read_csv('misc/data/music_features_embeddings.csv')
additional_extra['embedding'] = additional_extra['embedding'].apply(eval)
additional_embedding = np.array(additional_extra['embedding'].tolist())

# Setting the weight of the embedings
combined_embeddings = ((embeddings * 0.4 ) + (additional_embedding * 0.6))

def find_top_n_similar(target_embedding, embeddings, data, playlist_indices, n=10):
    similarity_scores = cosine_similarity(target_embedding, embeddings).flatten()
    sorted_indices = np.argsort(similarity_scores)[::-1]
    
    top_n_indices = []
    
    for index in sorted_indices:
        if index not in playlist_indices:
            top_n_indices.append(index)
        if len(top_n_indices) == n:
            break
            
    top_n_similar = data.iloc[top_n_indices].copy()
    top_n_similar.loc[:, 'similarity_score'] = similarity_scores[top_n_indices]
    
    return top_n_similar[['name', 'artist', 'similarity_score']]

def select_random_songs(file_path='misc/data/processed_music_info.csv', n=15):
    
    data = pd.read_csv(file_path)
    
    
    if len(data) < n:
        raise ValueError("The dataset does not contain enough songs to select.")
    
    # Randomly select n songs
    random_songs = data.sample(n)
    
    # Return the specified columns
    selected_columns = ['name', 'artist', 'danceability', 'energy', 'loudness', 'speechiness', 'acousticness', 'instrumentalness', 'liveness', 'valence', 'tags']
    return random_songs[selected_columns].to_dict(orient='records')

# Select 15 random songs
playlist = select_random_songs(n=15)


# Get the embeddings for the playlist songs
playlist_indices = []
for song in playlist:
    idx = data[(data['name'] == song['name']) & (data['artist'] == song['artist'])].index
    if not idx.empty:
        playlist_indices.append(idx[0])

# Calculate the mean embedding for the playlist
if playlist_indices:
    playlist_embeddings = combined_embeddings[playlist_indices]
    mean_playlist_embedding = np.mean(playlist_embeddings, axis=0).reshape(1, -1)
    
    # Find the top 10 similar songs to the mean playlist embedding, excluding the playlist songs
    top_10_recommendations = find_top_n_similar(mean_playlist_embedding, combined_embeddings, data, playlist_indices, n=10)
    
    # Display the top 10 recommendations
    print(top_10_recommendations)
else:
    print("No valid songs found in the playlist.")

# Extract features
features = dict()
feature_names = ["danceability", "energy", "loudness", "speechiness", "acousticness", "instrumentalness", "liveness", "valence"]

# Convert playlist to a pandas DataFrame
playlist_df = pd.DataFrame(playlist)

for feature in feature_names:
    features["min_" + feature] = playlist_df[feature].min()
    features["max_" + feature] = playlist_df[feature].max()

features["seed_genres"] = playlist_df['tags'].iloc[0].split(',')[:3]
features["seed_genres"] = ','.join(features["seed_genres"])

# Spotify credentials and API interaction
SPOTIFY_CLIENT_ID = '8fd2a7d8d5384d37bfa3b7ecb84f16c4'
SPOTIFY_CLIENT_SECRET = '6e10fb6c946e4a7f97613133907894c2'

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    print("Please set the SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables")
    exit(1)

# Initialize Spotipy
auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
spotify = spotipy.Spotify(auth_manager=auth_manager)

# Function to get recommendations
def get_recommendations(spotify, features, limit=10):
    recommendations = spotify.recommendations(
        seed_genres=features['seed_genres'].split(','),
        limit=limit,
        min_danceability=features['min_danceability'],
        max_danceability=features['max_danceability'],
        min_energy=features['min_energy'],
        max_energy=features['max_energy'],
        min_loudness=features['min_loudness'],
        max_loudness=features['max_loudness'],
        min_speechiness=features['min_speechiness'],
        max_speechiness=features['max_speechiness'],
        min_acousticness=features['min_acousticness'],
        max_acousticness=features['max_acousticness'],
        min_instrumentalness=features['min_instrumentalness'],
        max_instrumentalness=features['max_instrumentalness'],
        min_liveness=features['min_liveness'],
        max_liveness=features['max_liveness'],
        min_valence=features['min_valence'],
        max_valence=features['max_valence']
    )
    return recommendations

# Get recommendations from Spotify
recs_from_spotify = get_recommendations(spotify, features, limit=10)

# Process and display the recommendations
recs_from_spotify_list = []
for track in recs_from_spotify['tracks']:
    track_features = spotify.audio_features(track['id'])[0]
    recs_from_spotify_list.append({
        'name': track['name'],
        'danceability': track_features['danceability'],
        'energy': track_features['energy'],
        'loudness': track_features['loudness'],
        'speechiness': track_features['speechiness'],
        'acousticness': track_features['acousticness'],
        'instrumentalness': track_features['instrumentalness'],
        'liveness': track_features['liveness'],
        'valence': track_features['valence']
    })

recs_from_spotify_df = pd.DataFrame(recs_from_spotify_list)
# Print Spotify recommendations DataFrame
print("\nSpotify Recommendations DataFrame:")
print(recs_from_spotify_df)

top_10_recommendations = top_10_recommendations.merge(original_data, on=['name', 'artist'], how='left')

# Display the merged DataFrame with all features
print("\nTop 10 Recommendations with Features:")
print(top_10_recommendations)

# Ensure both DataFrames have the same columns for comparison
common_columns = recs_from_spotify_df.columns.intersection(top_10_recommendations.columns)
recs_from_spotify_df = recs_from_spotify_df[common_columns]
top_10_recommendations = top_10_recommendations[common_columns]


def calculate_euclidean_distance(v1, v2):
    return np.linalg.norm(v1 - v2)

def calculate_score(pd1, pd2):
    if pd1.shape[1] != pd2.shape[1]:
        print(pd1.shape[1])
        print(pd2.shape[1])
        raise ValueError("Dataframes must have the same number of features.")
    
    for _, x in pd1.iterrows():
        fx = np.array(x[1:].values)
        dist = list()
        for _, y in pd2.iterrows():
            fy = np.array(y[1:].values)
            dist.append(calculate_euclidean_distance(fx, fy))
        print(np.mean(dist))

calculate_score(top_10_recommendations, recs_from_spotify_df)