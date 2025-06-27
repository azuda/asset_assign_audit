import json
from dotenv import load_dotenv
import os
import requests
import sys
import urllib3

# ==========================================================================

with open('assets_assigned.json', 'r') as f:
  ASSETS = json.load(f)

load_dotenv()
ASSETSONAR_TOKEN = os.getenv('COMPANY_TOKEN')
ASSETSONAR_SUBDOMAIN = os.getenv('COMPANY_SUBDOMAIN')
BASE_URL = f'https://{ASSETSONAR_SUBDOMAIN}.assetsonar.com'
API_ENDPOINT = 'members.api'

# ==========================================================================

def get_as_users(page_num):
  """Fetch a single page of members from AssetSonar API

  Args:
    page_num (int): Page number to fetch

  Returns:
    dict: Response data as json, or None if an error occurs
  """
  url = f'{BASE_URL}/{API_ENDPOINT}'
  headers = {
    'token': ASSETSONAR_TOKEN,
    'Content-Type': 'application/x-www-form-urlencoded' # As per curl, though params are used for GET
  }
  params = {
    'include_custom_fields': 'true',
    'page': page_num
  }

  try:
    # curl  -H "token:<COMPANY_TOKEN>" -X GET -d "include_custom_fields=true" "https://<SUBDOMAIN>.assetsonar.com/members.api?page=<PAGE_NUM | DEFAULT = 1>"
    response = requests.get(url, headers=headers, params=params, timeout=30, verify=False)
  except requests.exceptions.RequestException as e:
    print(f'Error fetching page {page_num}: {e}', file=sys.stderr)
    if response is not None:
      print(f'Response content: {response.text}', file=sys.stderr)
    return None
  except json.JSONDecodeError:
    print(f'Error decoding JSON from response for page {page_num}: {response.text}', file=sys.stderr)
    return None
  return response.json()


def checkin_asset(asset_id):
  endpoint = f'assets/{asset_id}/checkin.api'
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


def checkout_asset(id, user):
  endpoint = f'assets/{id}/checkout.api?user_id={user}'
  url = f'{BASE_URL}/{endpoint}'
  headers = {
    'token': ASSETSONAR_TOKEN,
    'Content-Type': 'application/x-www-form-urlencoded' # As per curl, though params are used for GET
  }
  params = {
    'checkout_values[comments]': 'Auto checkout by AAA: https://github.com/azuda/asset_assign_audit',
  }

  response = requests.put(url, headers=headers, params=params, timeout=30, verify=False)
  return response.json()


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
  print(f'User with {email} not found in members list.', file=sys.stderr)
  return None


def get_all_assetsonar_users():
  print('--- Getting AssetSonar user data ---')

  all_users = []
  current_page = 1
  total_pages = 1  # initialize to 1
  while current_page <= total_pages:
    print(f'Fetching page {current_page}...')
    page_data = get_as_users(current_page)

    if page_data is None:
      print('Failed to retrieve page data. Aborting.', file=sys.stderr)
      break

    for user in page_data.get('members', []):
      if not isinstance(user, dict):
        print(f"Unexpected response format: 'members' contains non-dict item on page {current_page}.", file=sys.stderr)
        continue
      this_user = {}
      this_user['id'] = user['id']
      this_user['name'] = user['full_name']
      this_user['email'] = user['email']
      this_user['EGY'] = user.get('EGY', None)
      this_user['role'] = user['role_name']
      all_users.append(this_user)

    total_pages = page_data.get('total_pages', current_page)
    current_page += 1

    if not page_data and current_page > 1:
    # if current_page > 5:
      print('No more users found on subsequent pages.')
      break

  if all_users:
    with open('response_members.json', 'w') as f:
      json.dump(all_users, f, indent=2, sort_keys=True)
    print(f'All AssetSonar members saved to response_members.json - total: {len(all_users)}')
  else:
    print('No members retrieved or an error occurred')



# ==========================================================================

def main():
  # start

  get_all_assetsonar_users()

  all_reassigned = []
  # checkin assets in wrong_user and checkout to their jamf-assigned user
  for asset in ASSETS['wrong_user']:
    checkin_response = checkin_asset(asset['asset_id'])
    # print(f'Checked in asset {asset["serial_no"]}:')
    # print(checkin_response)
    checkout_response = checkout_asset(asset['asset_id'], get_user_id(asset['jamf_user_data']['email']))
    # print(f'Checked out asset {asset["serial_no"]} to user {asset["assigned_email"]}:')
    # print(checkout_response)
    all_reassigned.append({'serial_no': asset['serial_no'], 'checkin': checkin_response, 'checkout': checkout_response})
  
  # try to checkout unassigned assets to their jamf-assigned user
  for asset in ASSETS['unassigned']:
    jamf_user_data = asset.get('jamf_user_data')
    jamf_email = jamf_user_data.get('email') if jamf_user_data else None
    if jamf_email is None:
      all_reassigned.append({'serial_no': asset['serial_no'], 'checkin': 'UNASSIGNED', 'checkout': 'NO_EMAIL'})
    else:
      checkout_response = checkout_asset(asset['asset_id'], get_user_id(jamf_email))
      all_reassigned.append({'serial_no': asset['serial_no'], 'checkin': 'UNASSIGNED', 'checkout': checkout_response})

  with open('assets_reassigned.json', 'w') as f:
    json.dump(all_reassigned, f, indent=2, sort_keys=True)

  print('Done')

  # end

# ==========================================================================

if __name__ == '__main__':
  print(f'\n\n--- audit_users.py ---')
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  main()
