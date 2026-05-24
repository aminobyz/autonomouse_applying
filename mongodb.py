from pymongo import MongoClient
from datetime import datetime
import json

from websockets import client

class MongoDB:
    def __init__(self, database_name="mydatabase", collection_name="indeed"):
        self.database_name = database_name
        self.collection_name = collection_name

    # Connect to MongoDB         
    def connect(self):
        # With authentication
        client = MongoClient('mongodb://admin:admin@localhost:27017/')

        # Select database and collection
        db = client[self.database_name]
        collection = db[self.collection_name]

        ## Insert single document
        #user = {
        #    "name": "John Doe",
        #    "email": "john@example.com",
        #    "age": 30,
        #    "created_at": datetime.now()
        #}
        #result = collection.insert_one(user)
        #print(f"Inserted document with ID: {result.inserted_id}")
 
        ## Insert multiple documents
        #users = [
        #    {"name": "Alice", "email": "alice@example.com", "age": 25},
        #    {"name": "Bob", "email": "bob@example.com", "age": 35},
        #    {"name": "Charlie", "email": "charlie@example.com", "age": 28}
        #]
        #result = collection.insert_many(users)
        #print(f"Inserted {len(result.inserted_ids)} documents")
 
 
        ## Verify data
        #print("\nAll users in database:")
        #for user in collection.find():
        #    print(f"  {user['name']} - {user['email']}")

        return client, collection

    def disconnect(self, client):
        client.close()