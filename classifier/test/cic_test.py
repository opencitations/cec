import requests

url = "http://test.opencitations.net:81/cic/api/classify"

data = {
    "file": "<FILE>",
    "mode": "M"
}

response = requests.post(url, json=data)

if response.status_code == 200:
    print("Request successful!")
    print("Response data:", response.json())  # Print JSON response
else:
    print("Request failed with status code:", response.status_code)
    print("Error message:", response.text)
