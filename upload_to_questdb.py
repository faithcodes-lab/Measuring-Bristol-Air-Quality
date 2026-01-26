import requests
import os

# this script has to be in the same location as the 'sample_station_452.csv', 
# otherwise it will fail during execution as it won't be able to locate the csv.

FILE_PATH = 'sample_station_452.csv'
QUESTDB_URL = 'http://localhost:9000/imp'
TARGET_TABLE = 'reading'

def upload_data():
    if not os.path.exists(FILE_PATH):
        print(f"Error: '{FILE_PATH}' not found. Run generate_station_sample.py first.")
        return

    print(f"Uploading '{FILE_PATH}' to table '{TARGET_TABLE}'...")

    # I am using the QuestDB Import API and subsequently using the 
    # params={'name': 'reading'} to force it into the reading table 
    # previously created (create script provided in section 2.3 schema definition)
    try:
        with open(FILE_PATH, 'rb') as f:
            response = requests.post(
                QUESTDB_URL,
                params={'name': TARGET_TABLE},
                files={'data': f}
            )
        
        if response.status_code == 200:
            print("Success. Data imported into QuestDB.")
            print(f"Server Response: {response.text}")
        else:
            print("Error uploading data.")
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("Could not connect to QuestDB.")
        print("Is the server running at http://localhost:9000?")

if __name__ == "__main__":
    upload_data()