from huggingface_hub import hf_hub_download
import shutil
import os

repo_id = "Qwen/Qwen2.5-Math-72B-Instruct"
local_dir = r"c:\startingup\AIMO\AIMO_core\models\Qwen2.5-Math-72B-Instruct"
os.makedirs(local_dir, exist_ok=True)

filenames = ["tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt", "special_tokens_map.json", "generation_config.json"]
for fn in filenames:
    try:
        hf_hub_download(repo_id=repo_id, filename=fn, local_dir=local_dir)
        print(f"Downloaded {fn}")
    except Exception as e:
        print(f"Error downloading {fn}: {e}")
