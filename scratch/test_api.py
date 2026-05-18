import requests
import json

url = "http://localhost:5176/api/solve/stream"
data = {"problem_text": "2+2"}
try:
    response = requests.post(url, json=data, stream=True)
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                print(line.decode('utf-8'))
    else:
        print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")
