import os
import requests
import json
from dotenv import load_dotenv
import csv
import certifi
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import sqlite3
import re

def main():
    print()



def retrieve_api():
    # Load environment variables from a .env file
    load_dotenv()

    # Retrieve the API key from the environment variables
    api_key = os.getenv("API_KEY")
    SHELTER_ID = os.getenv("SHELTER_ID")
    url = "https://api.adoptapet.com/search/pets_at_shelter?key="+api_key+"&output=json&end_number=100&shelter_id="+SHELTER_ID

    #perform a get request on url and format the json output
    response = requests.get(url, verify=certifi.where())
    json_data = response.json()
    # formatted_json = json.dumps(json_data, indent=4)

    '''
    Format for getting the website link to adoption:
    uri =
    "https://api.adoptapet.com/search/limited_pet_details?pet_id=" +
    petID +
    "&key=" +
    api_key +
    "&v=1&output=json";
    '''

    for pet in json_data['pets']:        
        pet_format = json.dumps(pet, indent=1)
        print(pet_format)
        details_url = pet['details_url']
        details_response = requests.get(details_url, verify=certifi.where())
        details_json_data = details_response.json()
        formatted_details_json = json.dumps(details_json_data, indent=1)
        # construct a timestamped filename in the format MM-dd-yyyy Name species.json
        pet_name = details_json_data.get('pet', {}).get('pet_name', pet.get('pet_name', 'unknown'))
        pet_species = details_json_data.get('pet', {}).get('species', pet.get('species', ''))
        # sanitize simple problematic characters in filename
        pet_name_safe = str(pet_name).replace('/', '-').replace('\\', '-').strip()
        pet_species_safe = str(pet_species).replace('/', '-').replace('\\', '-').strip()
        tfilename = f"{datetime.now().strftime('%m-%d-%Y')}  {pet_name_safe}  {pet_species_safe}.json"
        with open(tfilename, 'w') as f:
            f.write(formatted_details_json)
        
        break


def read_google_sheet(spreadsheet_id: str,
                      range_name: str = None,
                      creds_json_path: str = None,
                      output_format: str = 'json',
                      to_file: str = None):
    """Read a Google Sheet and output its contents.

    By default (output_format='json') this writes a timestamped JSON file instead of printing.

    Args:
        spreadsheet_id: ID of the spreadsheet (from the URL).
        range_name: Optional A1 notation range (e.g. 'Sheet1!A1:C100'). If None, reads the whole first sheet.
        creds_json_path: Path to service account JSON. If None, looks at env var GOOGLE_CREDS_JSON.
        output_format: 'json' (default), 'csv', 'table', or 'raw'.
        to_file: Optional explicit path to write output. If omitted and output_format=='json', a file
                 named '<MM-DD-YYYY> <sheet title>.json' will be created in the CWD.

    Returns:
        dict with keys 'header' and 'rows'.
    """
    if not creds_json_path:
        creds_json_path = os.getenv('GOOGLE_CREDS_JSON')

    if not creds_json_path or not os.path.exists(creds_json_path):
        raise FileNotFoundError('Google service account JSON not found. Set GOOGLE_CREDS_JSON or pass creds_json_path')

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets.readonly',
        'https://www.googleapis.com/auth/drive.readonly',
    ]

    creds = Credentials.from_service_account_file(creds_json_path, scopes=scopes)
    client = gspread.authorize(creds)

    sh = client.open_by_key(spreadsheet_id)
    worksheet = sh.sheet1
    values = worksheet.get(range_name) if range_name else worksheet.get_all_values()

    if not values:
        print('No data found for the given spreadsheet/range.')
        return {'header': [], 'rows': []}

    header = values[0]
    rows = values[1:]
    ncols = len(header)
    normalized_rows = []
    for r in rows:
        if len(r) < ncols:
            normalized_rows.append(r + [''] * (ncols - len(r)))
        else:
            normalized_rows.append(r[:ncols])

    # Helper to create a safe filename from sheet title
    def _safe_filename(s: str) -> str:
        bad = '\\/:*?"<>|'
        out = ''.join('-' if c in bad else c for c in s)
        out = ' '.join(out.split())
        return out

    # Default behavior: write JSON to a timestamped file
    if output_format == 'json':
        list_of_dicts = [ { header[i]: row[i] for i in range(ncols) } for row in normalized_rows ]
        json_text = json.dumps(list_of_dicts, indent=2, ensure_ascii=False)

        if to_file:
            with open(to_file, 'w', encoding='utf-8') as f:
                f.write(json_text)
            print(f'Wrote JSON to {to_file}')
        else:
            # build a filename from date and spreadsheet title
            title = getattr(sh, 'title', spreadsheet_id)
            filename = f"{datetime.now().strftime('%m-%d-%Y')} { _safe_filename(title) }.json"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json_text)
            print(f'Wrote JSON to {filename}')

    elif output_format == 'csv':
        import io
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(header)
        writer.writerows(normalized_rows)
        csv_text = buf.getvalue()
        if to_file:
            with open(to_file, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_text)
            print(f'Wrote CSV to {to_file}')
        else:
            print(csv_text)

    elif output_format == 'table':
        col_widths = [len(str(h)) for h in header]
        for r in normalized_rows:
            for i in range(ncols):
                col_widths[i] = max(col_widths[i], len(str(r[i])))

        sep = '+-' + '-+-'.join('-' * w for w in col_widths) + '-+'
        header_line = '| ' + ' | '.join(str(header[i]).ljust(col_widths[i]) for i in range(ncols)) + ' |'
        print(sep)
        print(header_line)
        print(sep)
        for r in normalized_rows:
            print('| ' + ' | '.join(str(r[i]).ljust(col_widths[i]) for i in range(ncols)) + ' |')
        print(sep)

    else:
        # raw
        print(values)

    return {'header': header, 'rows': normalized_rows}


def create_sheet_database(spreadsheet_id: str,
                         db_path: str = None,
                         table_name: str = None,
                         creds_json_path: str = None,
                         range_name: str = None) -> str:
    """Create an SQLite database from a Google Sheet's contents.
    
    Args:
        spreadsheet_id: The ID of the Google Sheet to read.
        db_path: Optional path for the SQLite database. If None, uses '<MM-DD-YYYY> <sheet title>.db'.
        table_name: Optional name for the table. If None, uses a sanitized version of the sheet title.
        creds_json_path: Optional path to Google service account JSON. If None, uses GOOGLE_CREDS_JSON env var.
        range_name: Optional A1 range to read from the sheet. If None, reads all data.
    
    Returns:
        Path to the created database file.
    """
    # Get sheet data using existing function
    data = read_google_sheet(spreadsheet_id, range_name, creds_json_path, output_format='raw')
    if not data['header']:
        raise ValueError('No data found in the sheet')

    # Helper to create SQL-safe identifiers
    def _sql_safe_name(s: str) -> str:
        # Replace non-alphanumeric with underscore, ensure starts with letter
        safe = re.sub(r'\W+', '_', s.strip())
        if safe[0].isdigit():
            safe = 'f_' + safe
        return safe.lower()

    # Get or create table name from sheet title
    if not table_name:
        sh = gspread.authorize(
            Credentials.from_service_account_file(
                creds_json_path or os.getenv('GOOGLE_CREDS_JSON'),
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
        ).open_by_key(spreadsheet_id)
        table_name = _sql_safe_name(getattr(sh, 'title', 'sheet_data'))

    # Create database path if not provided
    if not db_path:
        db_path = f"{datetime.now().strftime('%m-%d-%Y')} {table_name}.db"

    # Convert sheet headers to SQL column names
    columns = [_sql_safe_name(h) for h in data['header']]

    # Create SQLite database and table
    with sqlite3.connect(db_path) as conn:
        # Create table with TEXT columns (can store any data type)
        create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n    " + \
                    ",\n    ".join(f"{col} TEXT" for col in columns) + \
                    "\n)"
        
        conn.execute("DROP TABLE IF EXISTS " + table_name)
        conn.execute(create_sql)

        # Insert data
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"
        conn.executemany(insert_sql, data['rows'])

        # Create an index on the first column as it's likely a key
        index_name = f"idx_{table_name}_{columns[0]}"
        conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns[0]})")

        print(f"Created database '{db_path}' with table '{table_name}'")
        print(f"Columns: {', '.join(columns)}")
        print(f"Inserted {len(data['rows'])} rows")

    return db_path


if __name__ == "__main__":
    main()
    spreadsheet_id = "1hhh4JabejnfuNOLRbo97rGWkQ3zSlJ_0vH6HH4i1vWw"
    
    # Example: Create SQLite database from sheet
    db_path = create_sheet_database(
        spreadsheet_id,
        creds_json_path="./credentials.json"
    )
    print(f"\nDatabase created at: {db_path}")

# https://www.adoptapet.com/pet/46161281-east-hartford-connecticut-boxer-mix