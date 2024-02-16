import cv2
from typing import NoReturn
from threading import Thread
from time import sleep, time
from pathlib import Path
import os
import traceback
import sys

import logging

class CameraCapture:
    def __init__(self, delay: float, cameras: list[str], save_base_path: str) -> None:
        self.cameras = cameras
        self.delay = delay
        self.logger = logging.getLogger("")
        self.logger.info = print
        self.cv_cameras: list[cv2.VideoCapture] = []
        self.save_path = Path(save_base_path)
        self.thread: Thread = None

        self.save_path.mkdir(exist_ok=True)

    def close_cameras(self) -> None:
        # Close cameras
        for cam in self.cv_cameras:
            try:
                cam.release()
            except: pass

        self.cv_cameras.clear()

    def open_cameras(self) -> None:
        self.close_cameras()
        for cam in self.cameras:
            self.cv_cameras.append(cv2.VideoCapture(cam))

    def start(self) -> None:
        self.open_cameras()
        self.thread = Thread(target = self._thread_target, daemon = True)
        self.thread.start()

    def join(self):
        if self.thread is None: return
        self.thread.join()

    def _thread_target(self) -> NoReturn:
        
        print("[CAPTURE] Started capture thread")
        while True:
            
            for idx, cvcam in enumerate(self.cv_cameras):
                try:
                    filename = f'{int(time())}_cam{idx}.jpg'
                    print(f"[CAPTURE] Capturing from camera {idx} to {filename}")
                    success, img = cvcam.read()
                    if not success:
                        print(f"[CAPTURE] FAILED!", file=sys.stderr)
                        return
                    cv2.imwrite(os.path.join(self.save_path, filename), img)
                except Exception as excp:
                    traceback.print_exc()
                    return
                
            print(f"[CAPTURE] -- Sleeping {self.delay} seconds --")
            sleep(self.delay)