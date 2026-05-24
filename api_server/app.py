from typing import Any
import requests
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# A simple Python dictionary to act as our temporary database
fake_database = {}

# -------------------------------------------------------------
# 1. GET Request: Used to fetch or read data
# -------------------------------------------------------------
@app.get("/")
def get_pdf():
    return fake_database
#
#@app.get("/users/{user_id}")
#def get_user(user_id: int):
#    # Checks if the user exists in our dictionary
#    if user_id in fake_database:
#        return fake_database[user_id]
#    return {"error": "User not found"}


# -------------------------------------------------------------
# 2. POST Request: Used to send or create new data
# -------------------------------------------------------------
# We define a blueprint (Schema) for what data a user must send us
class NewUser(BaseModel):
    url: str
    website: str
    role: str
    date: str
    file_size: int 
    pdf_file: Any  # Optional field to store scraped data
 

@app.post("/test")
def create_user(user_data: NewUser):
    # Generate a new ID based on how many items we have
    new_id = len(fake_database) + 1
    
    # Save the incoming data into our dictionary database
    
    fake_database[0] = user_data
    
    return {"status": "User created successfully", "assigned_id": new_id, "data": user_data}


if __name__ == "__main__":    

    BASE_URL = "http://localhost:8000"

    # Send data
    response = requests.post(f"{BASE_URL}/test", 
                            json={"url": "https://www.indeed.com/jobs?q=data+scientist&l=remote", 
                                  "website": "Indeed", 
                                  "role": "Data Scientist", 
                                  "date": "2024-06-01",
                                  "file_size": 1024,
                                  "pdf_file": "This is a sample PDF content in string format."})
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")