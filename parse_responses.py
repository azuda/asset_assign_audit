import json
import urllib3

# aggregate responses obtained from AssetSonar and Jamf
# sort assets by good / need reassign / need to retire

# ==========================================================================

with open('response_assetsonar.json', 'r') as f:
  ASSETSONAR_DATA = json.load(f)

with open('response_jamf_computers.json', 'r') as f:
  JAMF_COMPUTERS = json.load(f)

with open('response_jamf_computer_users.json', 'r') as f:
  JAMF_COMPUTER_USERS = json.load(f)

with open('response_jamf_devices.json', 'r') as f:
  JAMF_DEVICES = json.load(f)

with open('response_jamf_device_users.json', 'r') as f:
  JAMF_DEVICE_USERS = json.load(f)

# ==========================================================================

def add_jamf_ids():
  """Get Jamf id from JAMF_COMPUTERS and JAMF_DEVICES and add to ASSETSONAR_DATA

  Returns:
    None
  """
  for asset in ASSETSONAR_DATA:
    computer = get_jamf_computer(asset['serial_no'])
    if computer:
      asset['jamf_id'] = computer['id']
    else:
      device = get_jamf_device(asset['serial_no'])
      if device:
        asset['jamf_id'] = device['id']
  return None


def add_jamf_users():
  """Get Jamf user and location info and add to ASSETSONAR_DATA

  Returns:
    None
  """
  for asset in ASSETSONAR_DATA:
    # user_data = get_jamf_user(asset['jamf_id']) if 'jamf_id' in asset else None
    user_data = get_jamf_user(asset['serial_no'])
    # print(user_data)
    if user_data:
      real_name = user_data.get('realName') or user_data.get('realname') or ''
      email = user_data.get('email') or user_data.get('emailAddress') or ''
      asset['jamf_user_data'] = {
        'username': user_data.get('username', ''),
        'real_name': real_name,
        'email': email
      }
  return None


def get_jamf_user(serial):
  """Get Jamf user info by device serial number

  Args:
    serial (str): Jamf device serial number

  Returns:
    dict: Jamf user info if found else None
  """
  computer = get_jamf_computer(serial)
  if computer is None:
    device = get_jamf_device(serial)

  jamf_id = computer['id'] if computer else device['id'] if device else None
  if jamf_id is None:
    print(f'sn {serial} not found in Jamf')
    return None

  for a in JAMF_COMPUTER_USERS['results']:
    if a['id'] == str(jamf_id):
      return a['userAndLocation']
  for b in JAMF_DEVICE_USERS['results']:
    if b['mobileDeviceId'] == str(jamf_id):
      return b['userAndLocation']

  print(f'User data for device {serial} not found')
  return None


def get_jamf_computer(sn):
  """Get Jamf computer info by serial number

  Args:
    sn (str): serial number of computer

  Returns:
    dict: Jamf computer info if found else None
  """
  for computer in JAMF_COMPUTERS['results']:
    if computer['hardware']['serialNumber'] == sn:
      return computer
  return None


def get_jamf_device(sn):
  """Get Jamf mobile device info by serial number

  Args:
    sn (str): serial number of mobile device

  Returns:
    dict: Jamf mobile device info if found else None
  """
  for device in JAMF_DEVICES['mobile_devices']:
    if device['serial_number'] == sn:
      return device
  return None


def sort_assignments(assets):
  """Sort assets to different lists based on AS vs Jamf assigned user and save to file

  Args:
    data (dict): parsed and combined AS / Jamf asset data

  Returns:
    None
  """
  good = []
  bad = []
  unassigned = []
  for asset in assets['assets_in_jamf']:
    if asset.get('jamf_user_data'):
      if asset['assigned_email'] == asset['jamf_user_data']['email']: # AS and Jamf emails match
        good.append(asset)
      elif asset['jamf_user_data']['email'] is None:                  # no email assigned in Jamf
        unassigned.append(asset)
      else:                                                           # asset assigned to incorrect email
        bad.append(asset)
    else:
      unassigned.append(asset)

  # populate data to send to .json
  result = {}
  result['correct_user'] = good
  result['wrong_user'] = bad
  result['unassigned'] = unassigned
  result['total_correct'] = len(good)
  result['total_wrong'] = len(bad)
  result['total_unassigned'] = len(unassigned)
  result['total_all'] = len(good) + len(bad) + len(unassigned)

  with open('assets_assigned.json', 'w') as f:
    json.dump(result, f, indent=2)
  print(f'Saved assets sorted by assignment to assets_assigned.json')

  return None

# ==========================================================================

def main():
  # start
  add_jamf_ids()
  add_jamf_users()

  in_jamf = []
  not_in_jamf = []
  for asset in ASSETSONAR_DATA:
    sn = asset['serial_no']
    if get_jamf_computer(sn) or get_jamf_device(sn): # sn grabbed from AS exists in Jamf
      in_jamf.append(asset)
    else:
      not_in_jamf.append(asset)

  result = {}
  result['assets_in_jamf'] = in_jamf
  result['not_in_jamf'] = not_in_jamf
  result['total_in_jamf'] = len(in_jamf)
  result['total_not_in_jamf'] = len(not_in_jamf)
  result['total_all'] = len(in_jamf) + len(not_in_jamf)

  # print(result)
  with open('assets.json', 'w') as f:
    json.dump(result, f, indent=2)
  print(f'Saved all checked out assets to assets.json')

  # generate assets_assigned.json
  sort_assignments(result)

  # done
  print('Done')

# ==========================================================================

if __name__ == '__main__':
  print(f'\n\n--- parse_responses.py ---')
  urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
  main()
