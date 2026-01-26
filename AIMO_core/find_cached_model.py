from huggingface_hub import snapshot_download
try:
    path = snapshot_download(repo_id="Qwen/Qwen2.5-Math-72B-Instruct", local_files_only=True)
    print("CACHED_PATH:", path)
except Exception as e:
    print("ERROR:", e)
