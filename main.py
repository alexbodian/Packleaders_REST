import os
import requests
import json
from dotenv import load_dotenv
import csv
import certifi

def main():
    # Load environment variables from a .env file
    load_dotenv()

    # Retrieve the API key from the environment variables
    api_key = os.getenv("API_KEY")
    SHELTER_ID = os.getenv("SHELTER_ID")
    url = "https://api.adoptapet.com/search/pets_at_shelter?key="+api_key+"&output=json&end_number=100&shelter_id="+SHELTER_ID

    #perform a get request on url and format the json output
    response = requests.get(url, verify=certifi.where())
    json_data = response.json()
    formatted_json = json.dumps(json_data, indent=4)
    for pet in json_data['pets']:        
        pet_id = pet['pet_id']
        print(pet)
        details_url = "https://api.adoptapet.com/search/pet_details?key="+api_key+"&output=json&id="+pet_id
        details_response = requests.get(details_url, verify=certifi.where())
        details_json_data = details_response.json()
        formatted_details_json = json.dumps(details_json_data, indent=1)
        print(formatted_details_json)


if __name__ == "__main__":
    main()
