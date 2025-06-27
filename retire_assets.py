import json
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

# ==========================================================================

with open('assets.json', 'r') as f:
  ASSETS = json.load(f)

load_dotenv()
ASSETSONAR_TOKEN = os.getenv('COMPANY_TOKEN')
ASSETSONAR_SUBDOMAIN = os.getenv('COMPANY_SUBDOMAIN')

BASE_URL = f'https://{ASSETSONAR_SUBDOMAIN}.assetsonar.com'

# ==========================================================================

def checkin_asset(id):
  endpoint = f'assets/{id}/checkin.api'
  url = f'{BASE_URL}/{endpoint}'
  headers = {
    'token': ASSETSONAR_TOKEN,
    'Content-Type': 'application/x-www-form-urlencoded' # As per curl, though params are used for GET
  }
  params = {
    'checkin_values[location_id]': 30681, # location == society office
  }

  response = requests.put(url, headers=headers, params=params, timeout=30, verify=False)
  return response.json()

def retire_asset(id):
  endpoint = f'assets/{id}/retire.api'
  url = f'{BASE_URL}/{endpoint}'
  headers = {
    'token': ASSETSONAR_TOKEN,
    'Content-Type': 'application/x-www-form-urlencoded' # As per curl, though params are used for GET
  }
  params = {
    'fixed_asset[retired_on]': datetime.today().strftime('%m/%d/%Y'),
    'fixed_asset[retire_reason_id]': 101650, # reason == deleted from jamf
  }

  response = requests.put(url, headers=headers, params=params, timeout=30, verify=False)
  return response.json()

# ==========================================================================

def main():
  retired = []

  for asset in ASSETS['not_in_jamf']:
    if asset['manufacturer'] != 'Apple':
      print(f"Skipping non-Apple asset: {asset['serial_no']}")
      continue
    this_asset = {}
    print(f'\n==========================================================================\n')
    response = checkin_asset(asset['asset_id'])
    print(f'Checked in asset {asset['serial_no']}: {response}')
    this_asset['checkin_response'] = response

    response = retire_asset(asset['asset_id'])
    print(f'Retired asset {asset['serial_no']}: {response}')
    this_asset['retire_response'] = response

    this_asset['serial_no'] = asset['serial_no']
    this_asset['name'] = asset.get('name', 'Unknown')
    retired.append(this_asset)

  with open('assets_retired.json', 'w') as f:
    json.dump(retired, f, indent=2)
  print(f'Retired {len(retired)} assets')
  print(f'List saved to assets_retired.json')
  print('Done')

# ==========================================================================

if __name__ == '__main__':
  print(f'\n\n--- retire_assets.py ---')
  main()
