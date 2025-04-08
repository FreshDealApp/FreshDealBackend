import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from src.models import db
from sqlalchemy import text
# Recommendation system Initiation

def get_purchase_data():
    # Bringing Completed data from the 'purchases' table
    query = text("SELECT user_id, listing_id FROM purchases WHERE status = 'COMPLETED'")  
    result = db.session.execute(query).fetchall()

    # Converting the result into a DataFrame
    df = pd.DataFrame(result, columns=['user_id', 'listing_id'])
    return df


def collaborative_filtering(df):
    # Create a pivot table of users based on their ids and listing id
    pivot_table = df.pivot_table(index='user_id', columns='listing_id', aggfunc='size', fill_value=0)

    # Compute the cosine similarity between users
    similarity_matrix = cosine_similarity(pivot_table)

    return similarity_matrix, pivot_table


def recommend_products(user_id, similarity_matrix, pivot_table):
    # Get the index of the user
    user_idx = pivot_table.index.get_loc(user_id)

    # Get the similarity scores for the user
    similarity_scores = similarity_matrix[user_idx]

    # Get similar users
    similar_users = list(pivot_table.index[similarity_scores > 0.5])  # Similarity threshold
    similar_users.remove(user_id)  # Remove the user itself

    # Get products bought by similar users (This is going to be updated)
    recommended_products = []
    for user in similar_users:
        user_products = pivot_table.loc[user][pivot_table.loc[user] > 0].index.tolist()
        recommended_products.extend(user_products)

    # Remove products already purchased by the target user
    purchased_products = pivot_table.loc[user_id][pivot_table.loc[user_id] > 0].index.tolist()
    recommended_products = [product for product in recommended_products if product not in purchased_products]

    return list(set(recommended_products))  # Remove duplicates


def get_recommendations_for_user(user_id):
    df = get_purchase_data()
    similarity_matrix, pivot_table = collaborative_filtering(df)
    recommendations = recommend_products(user_id, similarity_matrix, pivot_table)
    return recommendations
