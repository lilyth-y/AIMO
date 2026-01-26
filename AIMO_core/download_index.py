from huggingface_hub import hf_hub_download
import shutil
import os

repo_id = "Qwen/Qwen2.5-Math-72B-Instruct"
local_dir = r"c:\startingup\AIMO\AIMO_core\models\Qwen2.5-Math-72B-Instruct"
os.makedirs(local_dir, exist_ok=True)

try:
    hf_hub_download(repo_id=repo_id, filename="model.safetensors.index.json", local_dir=local_dir)
    print("Downloaded model.safetensors.index.json")
except Exception as e:
    print(f"Error: {e}")
