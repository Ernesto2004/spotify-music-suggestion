import pandas as pd
import numpy as np

# Load the CSV file
file_path = 'misc/data/music_info_with_embeddings.csv'
data = pd.read_csv(file_path)

# Convert the 'embedding' column from strings to lists
data['embedding'] = data['embedding'].apply(eval)

# Convert embeddings to a numpy array for efficient computation
embeddings = np.array(data['embedding'].tolist())


from sklearn.metrics.pairwise import cosine_similarity

def find_top_n_similar(target_embedding, embeddings, data,target_index, n=10):
    similarity_scores = cosine_similarity(target_embedding, embeddings).flatten()
    sorted_indices = np.argsort(similarity_scores)[::-1]
    
    top_n_unique_artists = []
    unique_artists_set = set()
    
    for index in sorted_indices:
        if index == target_index:
            continue
        if data.iloc[index]['artist'] not in unique_artists_set:
            top_n_unique_artists.append(index)
            unique_artists_set.add(data.iloc[index]['artist'])
        if len(top_n_unique_artists) == n:
            break
            
    top_n_similar = data.iloc[top_n_unique_artists].copy()
    top_n_similar.loc[:, 'similarity_score'] = similarity_scores[top_n_unique_artists]
    
    return top_n_similar[['name', 'artist', 'similarity_score']]

# Example usage: find top 10 unique artist recommendations for the first song
target_song_index = data[(data['name'] == 'Beat It') & (data['artist'] == 'Michael Jackson')].index[0]
target_embedding = embeddings[target_song_index].reshape(1, -1)
top_10_unique = find_top_n_similar(target_embedding, embeddings, data,target_song_index, n=10)

 #Display the top 10 recommendations
print(top_10_unique)