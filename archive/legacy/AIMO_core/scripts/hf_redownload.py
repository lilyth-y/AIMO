import os
import sys
import logging
from huggingface_hub import snapshot_download

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('hf_redownload')

REPO_ID = 'Qwen/Qwen2.5-Math-72B-Instruct'
LOCAL_DIR = r'C:\startingup\AIMO\AIMO_core\models\Qwen2.5-Math-72B-Instruct'

if __name__ == '__main__':
    token = os.environ.get('HUGGINGFACE_HUB_TOKEN')
    if not token:
        log.warning('HUGGINGFACE_HUB_TOKEN not set in environment. snapshot_download may still work if already logged in.')
    log.info('Starting snapshot_download for %s -> %s', REPO_ID, LOCAL_DIR)
    try:
        path = snapshot_download(repo_id=REPO_ID, local_dir=LOCAL_DIR, resume_download=True, token=token)
        log.info('snapshot_download finished. Local dir: %s', path)
    except Exception as e:
        log.exception('snapshot_download failed: %s', e)
        sys.exit(2)
