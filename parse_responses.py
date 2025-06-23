import json
import mail1

# ==========================================================================

# constants

with open('response_assetsonar.json', 'r') as f:
  ASSETSONAR_DATA = json.load(f)

with open('response_jamf_computers.json', 'r') as f:
  JAMF_COMPUTERS = json.load(f)

with open('response_jamf_devices.json', 'r') as f:
  JAMF_DEVICES = json.load(f)

# for asset in ASSETSONAR_DATA:
#   print(asset['serial_no'])

# for computer in JAMF_COMPUTERS['results']:
#   print(computer['hardware']['serialNumber'])

# for device in JAMF_DEVICES['mobile_devices']:
#   print(device['serial_number'])

# ==========================================================================

# functions

def get_jamf_computer(sn):
  for computer in JAMF_COMPUTERS['results']:
    if computer['hardware']['serialNumber'] == sn:
      return computer
  return None


def get_jamf_device(sn):
  for device in JAMF_DEVICES['mobile_devices']:
    if device['serial_number'] == sn:
      return device
  return None

# ==========================================================================

def main():
  # start
  in_jamf = []
  not_in_jamf = []

  for asset in ASSETSONAR_DATA:
    sn = asset['serial_no']
    if get_jamf_computer(sn) or get_jamf_device(sn):
      in_jamf.append(asset)
    else:
      not_in_jamf.append({'asset_id': asset['asset_id'], 'serial_no': sn})

  result = {}
  result['assets_in_jamf'] = in_jamf
  result['not_in_jamf'] = not_in_jamf
  result['total_in_jamf'] = len(in_jamf)
  result['total_not_in_jamf'] = len(not_in_jamf)
  result['total_all'] = len(in_jamf) + len(not_in_jamf)
  print(result)

  with open('assets.json', 'w') as f:
    json.dump(result, f, indent=2)





if __name__ == '__main__':
  main()
