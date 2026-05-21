import time
from multiprocessing import Event, Manager, Process, Queue

from detection.detection_loop import capture_detection_loop
from rendering.click_process import click_process
from rendering.transparent_window import transparent_window


CHECK_INTERVAL = 0.1
JOIN_TIMEOUT = 5


def start_processes(processes):
    """登録されたプロセスをすべて開始する。"""

    for process in processes:
        process.start()


def stop_processes(processes, stop_event):
    """全プロセスに停止を通知し、終了しない場合は強制終了する。"""

    stop_event.set()

    for process in processes:
        process.join(timeout=JOIN_TIMEOUT)

    for process in processes:
        if process.is_alive():
            process.terminate()
            process.join()


def wait_until_process_exits(processes):
    """いずれかのプロセスが終了するまで待機する。"""

    while all(process.is_alive() for process in processes):
        time.sleep(CHECK_INTERVAL)


def main():
    """YOLO検出、ウィンドウ描画、クリック処理を別プロセスで起動する。"""

    with Manager() as manager:
        detection_queue = Queue()
        detection_queue.cancel_join_thread()

        shared_position_data = manager.dict()
        stop_event = Event()

        processes = [
            Process(
                target=capture_detection_loop,
                args=(detection_queue, stop_event),
            ),
            Process(
                target=transparent_window,
                args=(detection_queue, shared_position_data, stop_event),
            ),
            Process(
                target=click_process,
                args=(detection_queue, shared_position_data, stop_event),
            ),
        ]

        try:
            start_processes(processes)
            wait_until_process_exits(processes)

        finally:
            stop_processes(processes, stop_event)
            print("Main process ended.")


if __name__ == "__main__":
    main()
