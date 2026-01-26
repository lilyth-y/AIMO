import os
import requests

snapshot_path = r"C:\Users\USER\.cache\huggingface\models--Qwen--Qwen2.5-Math-72B-Instruct\snapshots\8fcf92b1eac8eca48c3d49778ad3dd1b394c9a17"
tokenizer_url = "https://huggingface.co/Qwen/Qwen2.5-Math-72B-Instruct/resolve/main/tokenizer.json"
output_path = os.path.join(snapshot_path, "tokenizer.json")

try:
    response = requests.get(tokenizer_url)
    response.raise_for_status()
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    if os.path.exists(output_path):
        print("tokenizer.json downloaded successfully.")
    else:
        print("Download failed: file not found after writing.")

except requests.exceptions.RequestException as e:
    print(f"Download failed: {e}")
