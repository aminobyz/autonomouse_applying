import pymongo
from bson.binary import Binary
from pathlib import Path    
import pandas as pd

# Connect to your MongoDB
client = pymongo.MongoClient('mongodb://admin:admin@localhost:27017/')
db = client["mydatabase"]
collection = db["indeed"]

# 1. Read the PDF file into memory as bytes
pdf_path = Path("C:/Users/aminb/projects/automat_applying/loggedin_page.pdf")

print(pdf_path)

with open(pdf_path, "rb") as pdf_file:
    binary_pdf = Binary(pdf_file.read())

# 2. Build your document structure
document = {
    "filename": "loggedin_page.pdf",
    "description": "User uploaded resume",
    "file_data": binary_pdf  # Stored cleanly as binary data
}

# 3. Insert into MongoDB
result = collection.insert_one(document)
print(f"Successfully inserted PDF with Document ID: {result.inserted_id}")




# 1. Pull the data from MongoDB
cursor = collection.find()

# 2. Convert the cursor records directly into a Pandas DataFrame
df = pd.DataFrame(list(cursor))

print(df)


## Retrieve the document from the database
#stored_doc = collection.find_one({"filename": "sample_document.pdf"})
#
## Write the binary blob back into a physical file
#with open("downloaded_file.pdf", "wb") as output_file:
#    output_file.write(stored_doc["file_data"])