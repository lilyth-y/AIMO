from huggingface_hub import hf_hub_download
import shutil
import os

repo_id = "Qwen/Qwen2.5-Math-72B-Instruct"
local_dir = r"c:\startingup\AIMO\AIMO_core\models\Qwen2.5-Math-72B-Instruct"
os.makedirs(local_dir, exist_ok=True)

try:
    file_path = hf_hub_download(repo_id=repo_id, filename="config.json", local_dir=local_dir)
    print(f"Downloaded config.json to {file_path}")
except Exception as e:
    print(f"Error downloading config.json: {e}")
