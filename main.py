import os
import requests
import json
from dotenv import load_dotenv
import csv

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
  # Format and print the JSON response, then save to CSV
    try:
        formatted_response = json.loads(response.text)
        print(json.dumps(formatted_response, indent=4))

        # Extract array of objects if response is a dictionary containing an array
        if isinstance(formatted_response, dict):
            for key, value in formatted_response.items():
                if isinstance(value, list) and all(isinstance(item, dict) for item in value):
                    data_array = value
                    break
            else:
                print("No array of objects found in the JSON response to save as CSV.")
                return
        elif isinstance(formatted_response, list):
            data_array = formatted_response
        else:
            print("Response is not a list or a dictionary containing an array of objects.")
            return

        # Save the extracted array to CSV
        keys = set()
        for item in data_array:
            keys.update(item.keys())
        with open("response.csv", "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=sorted(keys))
            writer.writeheader()
            for item in data_array:
                writer.writerow({key: item.get(key, None) for key in keys})
        print("Response saved to 'response.csv'.")

    except json.JSONDecodeError as e:
        print("Response is not valid JSON:", response.text)
        print(f"JSONDecodeError: {e}")
   

if __name__ == "__main__":
    main()
