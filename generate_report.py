import json
from datetime import datetime
import csv

# ==========================================================================

def read(filename):
  with open(filename, 'r') as f:
    return json.load(f)

ALL_ASSETS = read('assets.json')
NO_JAMF_USER = read('assets_no_jamf_user.json')
RETIRED = read('assets_retired.json')

# ==========================================================================

def get_asset_status(asset):
  if asset.get('status') == 'retired':
    return 'Retired'
  elif asset.get('status') == 'active':
    return 'Active'
  elif asset.get('status') == 'inactive':
    return 'Inactive'
  else:
    return 'Unknown'

# ==========================================================================

def main():
  # start
  report = []
  for asset in ALL_ASSETS.get('assets_in_jamf', []):
    this = {}
    if asset['serial_no'] in NO_JAMF_USER:
      this['status'] = 'No Jamf User'
    else:
      this['status'] = 'Good'

    this['Serial Number'] = asset['serial_no']
    this['Device Name'] = asset['name']
    this['AssetSonar Email'] = asset.get('assigned_email')
    try:
      this['Jamf Email'] = asset['jamf_user_data']['email']
    except KeyError:
      this['Jamf Email'] = "N/A"
    # print(this)
    report.append(this)

  timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
  with open(f'reports/{timestamp}.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['Status', 'Serial Number', 'Device Name', 'AssetSonar Email', 'Jamf Email'])
    for row in report:
      writer.writerow(row.values())
  print(f'Created AssetSonar audit report {timestamp}.csv')

  #done
  print("Done")

# ==========================================================================

if __name__ == '__main__':
  print(f'\n\n--- generate_report.py ---')
  main()
