import json

# ==========================================================================

with open('response_assetsonar.json', 'r') as f:
  ASSETSONAR_DATA = json.load(f)

with open('response_jamf_computers.json', 'r') as f:
  JAMF_COMPUTERS = json.load(f)

with open('response_jamf_computer_users.json', 'r') as f:
  JAMF_COMPUTER_USERS = json.load(f)

with open('response_jamf_devices.json', 'r') as f:
  JAMF_DEVICES = json.load(f)

# ==========================================================================

def add_jamf_ids():
  """grab Jamf id from JAMF_COMPUTERS and JAMF_DEVICES and add to ASSETSONAR_DATA

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
  """grab Jamf user and location info and add to ASSETSONAR_DATA

  Returns:
    None
  """
  for asset in ASSETSONAR_DATA:
    user_data = get_jamf_user(asset['jamf_id']) if 'jamf_id' in asset else None
    # print(user_data)
    if user_data:
      asset['jamf_user_data'] = {'username': user_data['username'], 'real_name': user_data['realname'], 'email': user_data['email']}
  return None


def get_jamf_user(jamf_id):
  """get Jamf user info by Jamf id

  Args:
    id (str): Jamf user id

  Returns:
    dict: Jamf user info if found else None
  """
  for user in JAMF_COMPUTER_USERS['results']:
    if user['id'] == jamf_id:
      return user['userAndLocation']
  return None


def get_jamf_computer(sn):
  """get Jamf computer info by serial number

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
  """get Jamf mobile device info by serial number

  Args:
    sn (str): serial number of mobile device

  Returns:
    dict: Jamf mobile device info if found else None
  """
  for device in JAMF_DEVICES['mobile_devices']:
    if device['serial_number'] == sn:
      return device
  return None


def sort_assignments():
  with open('assets.json', 'r') as f:
    assets = json.load(f)

  good = []
  bad = []
  unassigned = []
  for asset in assets['assets_in_jamf']:
    if asset.get('jamf_user_data'):
      if asset['assigned_email'] == asset['jamf_user_data']['email']:
        good.append(asset)
      elif asset['jamf_user_data']['email'] is None:
        unassigned.append(asset)
      else:
        bad.append(asset)
    else:
      unassigned.append(asset)

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
    if get_jamf_computer(sn) or get_jamf_device(sn):
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

  # generate assets_assigned.json
  sort_assignments()

  # done
  print('Done')

# ==========================================================================

if __name__ == '__main__':
  print(f'\n\n--- parse_responses.py ---')
  main()
