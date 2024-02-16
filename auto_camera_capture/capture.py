import cv2
from typing import NoReturn
from threading import Thread
from time import sleep, time
from pathlib import Path
import os
import traceback

import logging

class CameraCapture:
    def __init__(self, delay: float, cameras: list[str], save_base_path: str) -> None:
        self.cameras = cameras
        self.delay = delay
        self.logger = logging.getLogger("")
        self.logger.info = print
        self.cv_cameras: list[cv2.VideoCapture] = []
        self.save_path = Path(save_base_path)

        self.save_path.mkdir(exist_ok=True)

    def open_cameras(self) -> None:
        for cam in self.cameras:
            self.cv_cameras.append(cv2.VideoCapture(cam))

    def start(self) -> None:
        self.open_cameras()
        Thread(target = self._thread_target, daemon = True).start()

    def _thread_target(self) -> NoReturn:
        
        self.logger.info("Started capture thread")
        while True:
            
            for idx, cvcam in enumerate(self.cv_cameras):
                try:
                    self.logger.info(f"Capturing from camera {idx}...")
                    success, img = cvcam.read()
                    if not success:
                        self.logger.error(f"FAILED!")
                        continue
                    filename = f'{int(time())}_cam{idx}.jpg'
                    self.logger.info(f'Saving as {filename}')
                    cv2.imwrite(os.path.join(self.save_path, filename), img)
                except Exception as excp:
                    traceback.print_exc()
                
            self.logger.info(f"Sleeping {self.delay} seconds")
            sleep(self.delay)