#!/usr/bin/env python
import os, traceback
from huggingface_hub import snapshot_download

LOG_PATH = os.path.join(os.path.dirname(__file__), 'reconstruct_log.txt')
def writelog(s):
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write(s + '\n')
    print(s)

try:
    repo_cache_name = 'models--Qwen--Qwen2.5-Math-72B-Instruct'
    writelog('repo_cache_name: ' + repo_cache_name)
    parts = repo_cache_name.split('--')
    repo_id = '/'.join(parts[1:]) if parts[0]=='models' else repo_cache_name
    writelog('Derived repo_id: ' + repo_id)

    cache_root = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')
    writelog('HF cache root: ' + cache_root)
    cache_folder = os.path.join(cache_root, 'hub', repo_cache_name)
    writelog('Cache folder exists: ' + str(os.path.isdir(cache_folder)))
    if os.path.isdir(cache_folder):
        try:
            writelog('\nListing top-level entries in cache folder:')
            for name in sorted(os.listdir(cache_folder))[:200]:
                writelog('- ' + name)
        except Exception:
            writelog('Error listing cache folder:')
            writelog(traceback.format_exc())

    writelog('\nCalling snapshot_download(local_files_only=True) ...')
    out = None
    try:
        out = snapshot_download(repo_id=repo_id, cache_dir=os.path.join(cache_root), local_files_only=True)
        writelog('\nsnapshot_download returned: ' + str(out))
        writelog('\nListing top-level of returned path:')
        try:
            for name in sorted(os.listdir(out))[:500]:
                writelog('- ' + name)
        except Exception:
            writelog('Error listing returned path:')
            writelog(traceback.format_exc())
    except Exception as e:
        writelog('\nsnapshot_download (local-only) failed with traceback:')
        writelog(traceback.format_exc())
        # Attempt online retry if local-only failed
        try:
            writelog('\nAttempting snapshot_download with network access (local_files_only=False).')
            writelog('If the model is private, ensure HUGGINGFACE_HUB_TOKEN or HUGGINGFACE_TOKEN is exported in the environment.')
            token = (os.environ.get('HUGGINGFACE_HUB_TOKEN') or os.environ.get('HUGGINGFACE_TOKEN')
                     or os.environ.get('HF_HUB_TOKEN') or os.environ.get('HF_TOKEN'))
            writelog('Found token in env: ' + str(bool(token)))
            out = snapshot_download(repo_id=repo_id, cache_dir=os.path.join(cache_root), local_files_only=False, token=token)
            writelog('\nOnline snapshot_download returned: ' + str(out))
            writelog('\nListing top-level of returned path:')
            try:
                for name in sorted(os.listdir(out))[:500]:
                    writelog('- ' + name)
            except Exception:
                writelog('Error listing returned path after online download:')
                writelog(traceback.format_exc())
        except Exception:
            writelog('\nOnline snapshot_download failed with traceback:')
            writelog(traceback.format_exc())

    writelog('\nDone')
except Exception:
    writelog('Fatal error:')
    writelog(traceback.format_exc())
