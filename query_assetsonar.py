##################################
## this is a modified ai script ##
##################################

# queries assetsonar for all checked out assets
# returns serial no. + device name

import requests
import json
import sys
from dotenv import load_dotenv
import os

# --- Configuration ---
# IMPORTANT: Replace with your actual AssetSonar details
# For security, consider using environment variables for sensitive data like tokens.
# Example: ASSETSONAR_TOKEN = os.getenv("ASSETSONAR_API_TOKEN")
# Example: ASSETSONAR_SUBDOMAIN = os.getenv("ASSETSONAR_SUBDOMAIN")

load_dotenv()
ASSETSONAR_TOKEN = os.getenv('COMPANY_TOKEN')  # Replace with your actual AssetSonar API Token
ASSETSONAR_SUBDOMAIN = os.getenv('COMPANY_SUBDOMAIN')  # Replace with your AssetSonar subdomain (e.g., yourcompany)

BASE_URL = f'https://{ASSETSONAR_SUBDOMAIN}.assetsonar.com'
API_ENDPOINT = '/assets/filter.api'

# --- Function to fetch assets from a single page ---
def fetch_assets_page(page_num, token, base_url, api_endpoint):
  """
  Fetches a single page of checked-out assets from the AssetSonar API.

  Args:
    page_num (int): The page number to fetch.
    token (str): The AssetSonar API token.
    base_url (str): The base URL of your AssetSonar instance.
    api_endpoint (str): The API endpoint for filtering assets.

  Returns:
    dict: The JSON response data for the page, or None if an error occurs.
  """
  url = f"{base_url}{api_endpoint}"
  headers = {
    'token': token,
    'Content-Type': 'application/x-www-form-urlencoded' # As per curl, though params are used for GET
  }
  params = {
    'status': 'checked_out',
    'include_custom_fields': 'true',
    'page': page_num
  }

  try:
    # AssetSonar API uses GET with query parameters for filters
    response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
    response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
    return response.json()
  except requests.exceptions.RequestException as e:
    print(f'Error fetching page {page_num}: {e}', file=sys.stderr)
    if response is not None:
      print(f'Response content: {response.text}', file=sys.stderr)
    return None
  except json.JSONDecodeError:
    print(f'Error decoding JSON from response for page {page_num}: {response.text}', file=sys.stderr)
    return None

# --- Main Script ---
def get_checked_out_serial_numbers():
  """
  Retrieves all checked-out asset serial numbers from AssetSonar.
  Handles pagination to fetch all available assets.

  Returns:
    list: A list of bios_serial_numbers, or an empty list if none are found or an error occurs.
  """
  all_checked_out_assets = []
  current_page = 1
  total_pages = 1 # Initialize to 1 to ensure the loop runs at least once

  print(f'Connecting to AssetSonar at: {BASE_URL}')

  while current_page <= total_pages:
    print(f'Fetching page {current_page}...')
    page_data = fetch_assets_page(current_page, ASSETSONAR_TOKEN, BASE_URL, API_ENDPOINT)

    if page_data is None:
      print('Failed to retrieve page data. Aborting.', file=sys.stderr)
      break

    # Check if 'assets' key exists and is a list
    assets_on_page = page_data.get('assets', [])
    if not isinstance(assets_on_page, list):
      print(f"Unexpected response format: 'assets' is not a list on page {current_page}.", file=sys.stderr)
      break

    # Extract bios_serial_number from each asset
    for asset in assets_on_page:
      asset_number = asset.get('sequence_num')
      serial_number = asset.get('bios_serial_number')
      device_name = asset.get('name', 'Unknown Device')
      assigned_email = asset.get('assigned_to_user_email')
      manufacturer = asset.get('manufacturer')
      if serial_number: # Only add if the serial number exists and is not empty
        this_device = {}
        this_device['asset_id'] = asset_number
        this_device['serial_no'] = serial_number
        this_device['name'] = device_name
        this_device['assigned_email'] = assigned_email
        this_device['manufacturer'] = manufacturer
        all_checked_out_assets.append(this_device)

    # Update total_pages from the response (it might be on the first page)
    # Safely get total_pages, default to current_page if not found, to avoid infinite loop
    total_pages = page_data.get('total_pages', current_page)

    # Increment for the next iteration
    current_page += 1

    # If the API indicates 0 assets, stop early
    if not assets_on_page and current_page > 1:
    # if current_page > 5:
      print('No more assets found on subsequent pages.')
      break

  print('\n--- All Checked-Out BIOS Serial Numbers ---')
  return all_checked_out_assets

if __name__ == '__main__':
  serial_numbers_dict = get_checked_out_serial_numbers()
  if serial_numbers_dict:
    with open('response_assetsonar.json', 'w') as f:
      json.dump(serial_numbers_dict, f, indent=2, sort_keys=True)
    print(f'AssetSonar data saved to response_assetsonar.json - total: {len(serial_numbers_dict)}')
  else:
    print('No serial numbers retrieved or an error occurred.')
