import time
import threading
from collections import deque

result_queue = deque()
queue_lock = threading.Lock()


def append_results(results):
    """生成結果をキューに追加する。"""

    with queue_lock:
        for item in results:
            result_queue.append(item)


def wait_for_results(timeout=5.0, poll_interval=0.05):
    """結果がキューに入るまで一定時間待ち、送信用の結果を返す。"""

    waited = 0

    while waited < timeout:
        with queue_lock:
            if result_queue:
                return list(result_queue)

        time.sleep(poll_interval)
        waited += poll_interval

    return []


def remove_sent_results(sent_results):
    """送信済みの結果をキューから削除する。"""

    with queue_lock:
        for item in sent_results:
            if item in result_queue:
                result_queue.remove(item)
