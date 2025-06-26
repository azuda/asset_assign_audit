import csv
import json
from dotenv import load_dotenv
import os
import requests
from datetime import datetime

# ==========================================================================

with open('to_checkin.csv', 'r') as f:
  reader = csv.reader(f)
  SERIALS = [row[0] for row in reader if row]

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
  return response.status_code, response.json()

# ==========================================================================

def main():
  # start

  checked_in = {'all': []}

  for sn in SERIALS:
    this_asset = {'serial_no': sn}
    asset = next((a for a in ASSETS['assets_in_jamf'] if a['serial_no'] == sn), None)
    if asset:
      status_code, response_json = checkin_asset(asset['asset_id'])
      if 200 <= status_code < 300:
        print(f'Checked in asset {sn}: {response_json}')
        this_asset['name'] = asset['name']
        this_asset['checkin_response'] = response_json
        checked_in['all'].append(this_asset)

  with open('assets_quick_checkin.json', 'w') as f:
    json.dump(checked_in, f, indent=2)

  print('Done')
  # done

# ==========================================================================

if __name__ == '__main__':
  main()
