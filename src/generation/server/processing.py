import io
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image

from models import generate_caption, generate_images
from queue_store import append_results


def decode_images(id_image_pairs):
    """受信した画像bytesをPIL Imageに変換する。"""

    decoded = []

    for rect_id, raw in id_image_pairs:
        try:
            image = Image.open(io.BytesIO(raw)).convert("RGB")
            decoded.append((rect_id, image))
        except Exception as error:
            print(f"[Decode Error] ID={rect_id}, Error: {error}")

    return decoded


def split_into_batches(items, batch_size=3):
    """リストを指定サイズごとのバッチに分割する。"""

    return [
        items[i:i + batch_size]
        for i in range(0, len(items), batch_size)
    ]


def generate_captions_parallel(decoded_images):
    """複数画像のcaptionを並列に生成する。"""

    results = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(generate_caption, image): rect_id
            for rect_id, image in decoded_images
        }

        for future in as_completed(futures):
            rect_id = futures[future]

            try:
                caption = future.result()
                results.append((rect_id, caption))
            except Exception as error:
                print(f"[Caption Error] ID={rect_id}, Error: {error}")

    return results


def process_uploaded_pairs(id_image_pairs):
    """画像のdecode、caption生成、画像生成、結果保存をまとめて実行する。"""

    decoded_images = decode_images(id_image_pairs)

    if not decoded_images:
        return

    caption_results = generate_captions_parallel(decoded_images)

    for batch in split_into_batches(caption_results):
        generated_results = generate_images(batch)
        append_results(generated_results)
