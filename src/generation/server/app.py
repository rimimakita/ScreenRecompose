from flask import Flask, request, Response, after_this_request
from flask_cors import CORS
import threading
import json
import base64
import time

from models import init_models
from processing import process_uploaded_pairs
from queue_store import (
    wait_for_results,
    remove_sent_results,
)

app = Flask(__name__)
CORS(app)


@app.route("/process_batch", methods=["POST"])
def process_batch():
    """受け取った画像バッチを別スレッドで処理開始する。"""

    files = request.files
    id_image_pairs = [
        (rect_id, files[rect_id].read())
        for rect_id in files
    ]

    threading.Thread(
        target=process_uploaded_pairs,
        args=(id_image_pairs,),
        daemon=True,
    ).start()

    return "Accepted", 202


@app.route("/get_results", methods=["GET"])
def get_all_results():
    """生成済みの画像とcaptionをJSON形式で返す。"""

    results_to_send = wait_for_results(
        timeout=5.0,
        poll_interval=0.05,
    )

    if not results_to_send:
        return "", 204

    json_data = []
    for rect_id, jpeg_bytes, caption in results_to_send:
        b64_image = base64.b64encode(jpeg_bytes).decode("utf-8")
        json_data.append({
            "id": rect_id,
            "image": b64_image,
            "caption": caption,
        })

    @after_this_request
    def _(response):
        remove_sent_results(results_to_send)
        return response

    return Response(
        json.dumps(json_data),
        status=200,
        mimetype="application/json",
    )


if __name__ == "__main__":
    init_models()
    app.run(host="0.0.0.0", port=5000)
