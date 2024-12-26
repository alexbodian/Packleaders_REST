import os
import requests
import json
from dotenv import load_dotenv

def main():
    # Load environment variables from a .env file
    load_dotenv()

    # Retrieve the API key from the environment variables
    api_key = os.getenv("API_KEY")
    SHELTER_ID = os.getenv("SHELTER_ID")
    url = "https://api.adoptapet.com/search/pets_at_shelter?key="+api_key+"&output=json&end_number=500&shelter_id="+SHELTER_ID

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

        # Format and print the JSON response
    try:
        formatted_response = json.loads(response.text)
        print(json.dumps(formatted_response, indent=4))
    except json.JSONDecodeError:
        print("Response is not valid JSON:", response.text)
   

if __name__ == "__main__":
    main()
