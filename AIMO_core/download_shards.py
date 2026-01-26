from huggingface_hub import hf_hub_download
import os

repo_id = "Qwen/Qwen2.5-Math-72B-Instruct"
local_dir = r"c:\startingup\AIMO\AIMO_core\models\Qwen2.5-Math-72B-Instruct"
os.makedirs(local_dir, exist_ok=True)

# Download all shards
for i in range(1, 38):
    filename = f"model-{i:05d}-of-00037.safetensors"
    if os.path.exists(os.path.join(local_dir, filename)):
        print(f"Skipping {filename} (exists)")
        continue
    try:
        print(f"Downloading {filename}...")
        hf_hub_download(repo_id=repo_id, filename=filename, local_dir=local_dir)
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
