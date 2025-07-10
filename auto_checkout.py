##################################
## this is a modified ai script ##
##################################

# queries assetsonar for all checked IN assets
# returns serial no. + device name

import requests
import json
import sys
from dotenv import load_dotenv
import os
import urllib3


load_dotenv()
ASSETSONAR_TOKEN = os.getenv('COMPANY_TOKEN')  # Replace with your actual AssetSonar API Token
ASSETSONAR_SUBDOMAIN = os.getenv('COMPANY_SUBDOMAIN')  # Replace with your AssetSonar subdomain (e.g., yourcompany)
BASE_URL = f'https://{ASSETSONAR_SUBDOMAIN}.assetsonar.com'
API_ENDPOINT = 'assets/filter.api'


def fetch_assets_page(page_num, token, base_url, api_endpoint):
  """
  Fetches a single page of checked in assets from the AssetSonar API.

  Args:
    page_num (int): The page number to fetch.
    token (str): The AssetSonar API token.
    base_url (str): The base URL of your AssetSonar instance.
    api_endpoint (str): The API endpoint for filtering assets.

  Returns:
    dict: The JSON response data for the page, or None if an error occurs.
  """
  url = f"{base_url}/{api_endpoint}"
  headers = {
    'token': token,
    'Content-Type': 'application/x-www-form-urlencoded' # As per curl, though params are used for GET
  }
  params = {
    'status': 'available',
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

def get_available_serial_numbers():
  """
  Retrieves all checked in asset serial numbers from AssetSonar.
  Handles pagination to fetch all available assets.

  Returns:
    list: A list of bios_serial_numbers, or an empty list if none are found or an error occurs.
  """
  all_available_assets = []
  current_page = 1
  total_pages = 1 # Initialize to 1 to ensure the loop runs at least once

  # print(f'Connecting to AssetSonar at: {BASE_URL}')
  print('Getting available assets data...')

  while current_page <= total_pages:
    # print(f'Fetching page {current_page}...')
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
      assigned_email = asset.get('candidate_email')
      manufacturer = asset.get('manufacturer')
      if serial_number: # Only add if the serial number exists and is not empty
        this_device = {}
        this_device['asset_id'] = asset_number
        this_device['serial_no'] = serial_number
        this_device['name'] = device_name
        this_device['assigned_email'] = assigned_email
        this_device['manufacturer'] = manufacturer
        all_available_assets.append(this_device)

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

  # print('\n--- All Checked in BIOS Serial Numbers ---')
  return all_available_assets

def checkout_asset(id, user):
  endpoint = f'assets/{id}/checkout.api?user_id={user}'
  url = f'{BASE_URL}/{endpoint}'
  headers = {
    'token': ASSETSONAR_TOKEN,
    'Content-Type': 'application/x-www-form-urlencoded'
  }
  params = {
    'checkout_values[comments]': 'Auto checkout by AAA: https://github.com/azuda/asset_assign_audit',
  }
  try:
    response = requests.put(url, headers=headers, params=params, timeout=60, verify=False)
    return response.json()
  except requests.exceptions.ReadTimeout:
    print(f"Timeout during checkout for asset {id}. Skipping.", file=sys.stderr)
    return {'error': 'timeout'}
  except Exception as e:
    print(f"Error during checkout for asset {id}: {e}", file=sys.stderr)
    return {'error': str(e)}

def get_user_id(email):
  """Get user id from email address

  Args:
    email (str): User email address

  Returns:
    int: User id if found else None
  """
  with open('response_members.json', 'r') as f:
    MEMBERS = json.load(f)
  if not isinstance(MEMBERS, list):
    print('Error: response_members.json does not contain a list of members.', file=sys.stderr)
    return None

  for user in MEMBERS:
    if user.get('email') == email:
      return user['id']
  # print(f'User with {email} not found in members list.', file=sys.stderr)
  return None


if __name__ == '__main__':
  print(f'\n\n--- auto_checkout.py ---')
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  serial_numbers_dict = get_available_serial_numbers()
  if serial_numbers_dict:
    with open('response_assetsonar_available.json', 'w') as f:
      json.dump(serial_numbers_dict, f, indent=2, sort_keys=True)
    print(f'AssetSonar data saved to response_assetsonar_available.json - total: {len(serial_numbers_dict)}')
  else:
    print('No serial numbers retrieved or an error occurred.')

  # try to assign devices
  all_checkout = []
  for asset in serial_numbers_dict:
    checkout_response = checkout_asset(asset['asset_id'], get_user_id(asset['assigned_email']))
    all_checkout.append({'serial_no': asset['serial_no'], 'checkout': checkout_response})
  with open('assets_autocheckout.json', 'w') as f:
    json.dump(all_checkout, f, indent=2, sort_keys=True)
  print(f'Checkout responses saved to assets_autocheckout.json - total: {len(all_checkout)}')
  print('Done')
