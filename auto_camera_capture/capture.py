import cv2
from typing import NoReturn
from threading import Thread
from time import sleep, time
from pathlib import Path
import os
import traceback
import sys
from auto_camera_capture.nc import NextCloudSync
from threading import Lock
import os
import glob

import logging

FOLDER_CLEANUP_TRIGGER = 1e10 # 10 Gb

class CameraCapture:
    def __init__(self, delay: float, cameras: list[str], save_base_path: str, nc_sync_urls: list[str] = None, show: bool = True) -> None:
        self.cameras = cameras
        self.delay = delay
        self.show = show
        self.cv_cameras: list[cv2.VideoCapture] = []
        
        self.save_path = Path(save_base_path)
        self.save_path.mkdir(exist_ok=True)

        self.thread: Thread = None
        self.lock = Lock()
        self.sync = NextCloudSync(self.save_path, nc_sync_urls, lock = self.lock)


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

    def _get_folder_size(self, path: Path) -> int:
        size = 0
        for path, dirs, files in os.walk(path):
            for f in files:
                fp = os.path.join(path, f)
                size += os.path.getsize(fp)
        return size

    def _show_image(self, img):
        cv2.namedWindow("bw", cv2.WND_PROP_FULLSCREEN)          
        cv2.setWindowProperty("bw", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow("bw", img)
        cv2.waitKey(1) & 0xFF == ord('0')

    def _thread_target(self) -> NoReturn:
        print("[CAPTURE] Started capture thread")
        while True:
            current_folder = self.save_path/str(int(time()))
            current_folder.mkdir(exist_ok=True)
            for idx, cvcam in enumerate(self.cv_cameras):
                try:
                    filename = f'cam{idx}.jpg'
                    print(f"[CAPTURE] Capturing from camera {idx} to {filename}")
                    success, img = cvcam.read()
                    if not success:
                        print(f"[CAPTURE] FAILED!", file=sys.stderr)
                        return
                    if self.show:
                        self._show_image(img)
                    cv2.imwrite(str(current_folder/filename), img)
                except Exception as excp:
                    traceback.print_exc()
                    return
            
            s = self._get_folder_size(self.save_path)
            print(f'[CAPTURE] Current save directory is {s} bytes')
            if s > FOLDER_CLEANUP_TRIGGER:
                print(f'[CAPTURE] Cleaning up save directory')
                with self.lock:
                   import shutil
                   files = glob.glob(f'{str(self.save_path)}/*')
                   for f in files:
                       shutil.rmtree(f)
                
            print(f"[CAPTURE] -- Sleeping {self.delay} seconds --")
            sleep(self.delay)