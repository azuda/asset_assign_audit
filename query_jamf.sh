#!/bin/sh

# query jamf for computer and device data
# https://developer.jamf.com/jamf-pro/docs/client-credentials

source "./.env"
url=$JAMF_URL
client_id=$CLIENT_ID
client_secret=$CLIENT_SECRET

getAccessToken() {
  response=$(curl --silent --location --request POST "${url}/api/oauth/token" \
    --header "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "client_id=${client_id}" \
    --data-urlencode "grant_type=client_credentials" \
    --data-urlencode "client_secret=${client_secret}")
  access_token=$(echo "$response" | plutil -extract access_token raw -)
  token_expires_in=$(echo "$response" | plutil -extract expires_in raw -)
  token_expiration_epoch=$(($current_epoch + $token_expires_in - 1))
}

checkTokenExpiration() {
  current_epoch=$(date +%s)
    if [[ token_expiration_epoch -ge current_epoch ]]
    then
      echo "Token valid until the following epoch time: " "$token_expiration_epoch" "($(date -r $token_expiration_epoch "+%Y-%m-%d %H:%M:%S"))"
    else
      echo "No valid token available, getting new token"
      getAccessToken
    fi
}

invalidateToken() {
  responseCode=$(curl -w "%{http_code}" -H "Authorization: Bearer ${access_token}" $url/api/v1/auth/invalidate-token -X POST -s -o /dev/null)
  if [[ ${responseCode} == 204 ]]
  then
    echo "Token successfully invalidated"
    access_token=""
    token_expiration_epoch="0"
  elif [[ ${responseCode} == 401 ]]
  then
    echo "Token already invalid"
  else
    echo "An unknown error occurred invalidating the token"
  fi
}

# start
checkTokenExpiration
curl -H "Authorization: Bearer $access_token" $url/api/v1/jamf-pro-version -X GET
checkTokenExpiration

# get all computers from jamf
curl -X "GET" \
  "$JAMF_URL/api/v1/computers-inventory?section=HARDWARE&page=0&page-size=2000&sort=id%3Aasc" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $access_token" > response_jamf_computers.json
echo "--- Jamf computers saved to response_jamf_computers.json ---"

# get all mobile devices from jamf
curl -X "GET" \
  "$JAMF_URL/JSSResource/mobiledevices" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $access_token" > response_jamf_devices.json
echo "--- Jamf mobile devices saved to response_jamf_devices.json ---"

# get all computers from jamf w user + location data
curl -X "GET" \
  "$JAMF_URL/api/v1/computers-inventory?section=USER_AND_LOCATION&page=0&page-size=2000&sort=general.name%3Aasc" \
  -H "accept: application/json" \
  -H "Authorization: Bearer $access_token" > response_jamf_computer_users.json
echo "--- Jamf computer users saved to response_jamf_computer_users.json ---"

# get all mobile devices from jamf w user + location data
curl -X 'GET' \
  'https://rundle.jamfcloud.com/api/v2/mobile-devices/detail?section=USER_AND_LOCATION&page=0&page-size=2000&sort=displayName%3Aid' \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $access_token" > response_jamf_device_users.json
echo "--- Jamf mobile users saved to response_jamf_device_users.json ---"

# kill api access token
invalidateToken
curl -H "Authorization: Bearer $access_token" $url/api/v1/jamf-pro-version -X GET
printf "\nDone query_jamf.sh"
