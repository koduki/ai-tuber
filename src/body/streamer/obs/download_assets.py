"""OBS 起動前にキャラクターアセットをストレージからダウンロードする。

StorageClient を使用して、ローカル (data/) または GCS から
キャラクター画像・BGM を /app/assets/ に配置します。
"""
import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("download_assets")

def main():
    character = os.getenv("CHARACTER_NAME", "ren")
    dest_dir = os.getenv("ASSETS_DIR", "/app/assets")
    
    logger.info(f"Downloading assets for character: {character}")
    logger.info(f"Storage type: {os.getenv('STORAGE_TYPE', 'filesystem')}")
    logger.info(f"Destination: {dest_dir}")
    
    os.makedirs(dest_dir, exist_ok=True)
    
    try:
        from infra.storage_client import create_storage_client
        storage = create_storage_client()
    except Exception as e:
        logger.error(f"Failed to initialize StorageClient: {e}")
        sys.exit(1)
    
    success_count = 0
    fail_count = 0
    
    prefix = f"mind/{character}/assets/"
    try:
        asset_keys = storage.list_objects(prefix=prefix)
    except Exception as e:
        logger.error(f"Failed to list assets: {e}")
        sys.exit(1)

    if not asset_keys:
        logger.warning(f"No assets found with prefix: {prefix}")

    for key in asset_keys:
        filename = os.path.basename(key)
        if not filename:
            continue

        dest = os.path.join(dest_dir, filename)
        
        try:
            storage.download_file(key=key, dest=dest)
            logger.info(f"  ✓ {filename}")
            success_count += 1
        except Exception as e:
            logger.error(f"  ✗ {filename} failed: {e}")
            fail_count += 1
    
    # 完了マーカーファイルを作成（OBS 起動ガード用）
    marker_path = os.path.join(dest_dir, ".assets_ready")
    with open(marker_path, "w") as f:
        f.write(f"ok: {success_count} downloaded, {fail_count} failed\n")
    
    logger.info(f"Asset download complete: {success_count} ok, {fail_count} failed")
    
    if fail_count > 0 and success_count == 0:
        logger.error("All assets failed to download. Exiting with error.")
        sys.exit(1)


if __name__ == "__main__":
    main()
