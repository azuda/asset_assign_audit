import os
from dotenv import load_dotenv
import requests
import json

# ===============================================================

# constants
load_dotenv()
COMPANY_TOKEN = os.getenv('COMPANY_TOKEN')
COMPANY_SUBDOMAIN = os.getenv('COMPANY_SUBDOMAIN')
AS_HEADERS = {
  'token': COMPANY_TOKEN,
}
AS_URL = f'https://{COMPANY_SUBDOMAIN}.assetsonar.com/'

# ===============================================================

# curl  -H "token:<COMPANY_TOKEN>" -X GET -d "status=checked_out" https://<SUBDOMAIN>.assetsonar.com/assets/filter.api?page=<PAGE_NUM | DEFAULT = 1>
page_num = 1
all_results = {}
# while True:
while page_num <= 5:
  try:
    print(f'Now fetching page {page_num}')
    response = requests.get(f'{AS_URL}assets/filter.api?page={page_num}', headers=AS_HEADERS, data={'status': 'checked_out'}, verify=False)
  except:
    print(f'End of pages @ page {page_num}')
    break

  try:
    data = json.loads(response.text)
  except json.JSONDecodeError:
    print(f'Could not decode JSON on page {page_num}')
    break

  results = data.get('rows', data)
  if not results:
    break
  all_results[page_num] = (results)
  print(all_results)
  page_num += 1

# response = requests.get(f'{AS_URL}assets/filter.api?page={page_num}', headers=AS_HEADERS, data={'status': 'checked_out'}, verify=False)
# data = response.text
# all_results.extend(data)

# write response to file
with open('response.json', 'w') as f:
  json.dump(all_results, f, indent=2)

with open('response.json') as f:
  data = json.load(f)

with open('response.json', 'w') as f:
  json.dump(data, f, indent=2, sort_keys=True)
