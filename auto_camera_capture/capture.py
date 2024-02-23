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
import random
import string
 
FOLDER_CLEANUP_TRIGGER = 2e10 # 20 Gb
def random_string_generator(str_size, allowed_chars = string.ascii_letters+string.digits) -> str:
    return ''.join(random.choice(allowed_chars) for x in range(str_size))

window_name = "window"
interframe_wait_ms = 30


import cv2
import numpy as np


_FULL_FRAMES = {}


def show_fullscreen(image, background_colour = None, window_name='window', display_number = 0, display_sizes=None):
    """
    Draw a fullscreen image.

    :param image: The image to show.
        If integer, it will be assumed to be in range [0..255]
        If float, it will be assumed to be in range [0, 1]
    :param background_colour: The background colour, as a BGR tuple.
    :param window_name: Name of the window (can be used to draw multiple fullscreen windows)
    :param display_number: Which monitor to display to.
    :param display_sizes: Size of displays (needed only if adding a background colour)
    """
    if image.dtype=='float':
        image = (image*255.999).astype(np.uint8)
    else:
        image = image.astype(np.uint8, copy=False)
    if image.ndim==2:
        image = image[:, :, None]

    assert display_number in (0, 1), 'Only 2 displays supported for now.'
    if window_name not in _FULL_FRAMES:
        cv2.namedWindow(window_name, cv2.WND_PROP_FULLSCREEN)
        if display_number == 1:
            assert display_sizes is not None
            first_display_size = display_sizes[0]
            cv2.moveWindow(window_name, *first_display_size)
        cv2.setWindowProperty(window_name,cv2.WND_PROP_FULLSCREEN,cv2.WINDOW_FULLSCREEN)
        if background_colour is not None:
            background_colour = np.array(background_colour)
            if background_colour.dtype=='int':
                background_colour = background_colour.astype(np.uint8)
            else:
                background_colour = (background_colour*255.999).astype(np.uint8)
            assert display_sizes is not None, "Unfortunately, if you want to specify background color you need to specify display sizes."
            pic_display_size = display_sizes[display_number]
            aspect_ratio = pic_display_size[1]/float(pic_display_size[0])  # (hori/vert)
            frame_size_x = int(max(image.shape[0]/aspect_ratio, image.shape[1]))
            frame_size_y = int(max(image.shape[1]*aspect_ratio, image.shape[0]))
            _FULL_FRAMES[window_name] = np.zeros((frame_size_y, frame_size_x, 3), dtype=np.uint8) + background_colour
        else:
            _FULL_FRAMES[window_name] = None

    if _FULL_FRAMES[window_name] is not None:
        frame = _FULL_FRAMES[window_name]
        start_y, start_x = (frame.shape[0] - image.shape[0])//2, (frame.shape[1] - image.shape[1])//2
        frame[start_y: start_y+image.shape[0], start_x:start_x+image.shape[1]] = image
        display_img = frame
    else:
        display_img = image

    cv2.imshow(window_name, display_img)
    cv2.waitKey(interframe_wait_ms)

class CameraCapture:
    def __init__(self, delay: float, cameras: list[str], save_base_path: str, nc_sync_urls: list[str] = None, show: str = None) -> None:
        self.cameras = cameras
        self.delay = delay
        self.show = show
        self.cv_cameras: list[cv2.VideoCapture] = []
        self.stream_camera_name = show
        self.stream_continue = True
        
        self.save_path = Path(save_base_path)
        self.save_path.mkdir(exist_ok=True)

        self.thread: Thread = None
        self.lock = Lock()
        self.sync = NextCloudSync(self.save_path, nc_sync_urls, lock = self.lock)
        self.stream_lock = Lock()
        Thread(target=self._start_stream, daemon=True).start()

    def begin_stream(self):
        if self.stream_camera_name is None: return
        self.stream_continue = True

    def _start_stream(self):
        if self.stream_camera_name is not None:

            while True:
                while not self.stream_continue:
                    sleep(0.1)
                print(f"[STREAM] Start streaming from {self.stream_camera_name}")
                cap = cv2.VideoCapture(self.stream_camera_name)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                if not cap.isOpened():
                    print("[STREAM] Error: Could not open video.")
                    return
                while self.stream_continue:
                    ret, frame = cap.read()
                    if not ret:
                        print("[STREAM] Reached end of video")
                        break
                    show_fullscreen(frame, (0, 0, 0), display_sizes=[[1024, 600]])
                cap.release()
                print("[STREAM] Stop stream!")


    def close_cameras(self) -> None:
        # Close cameras
        for cam in self.cv_cameras:
            try:
                cam.release()
            except: pass

        self.cv_cameras.clear()

    def open_cameras(self) -> None:
        return 
        self.close_cameras()
        for cam in self.cameras:
            
            self.cv_cameras.append(camm)

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
        imS = cv2.resize(img, (1024, 600)) # for expo
        cv2.waitKey(1) & 0xFF == ord('0')

    def _thread_target(self) -> NoReturn:
        print("[CAPTURE] Started capture thread")
        while True:
            print("[CAPTURE] Capturing...")
            self.stream_continue = False
            sleep(1)
            current_folder = self.save_path/f'{str(int(time()))}_{random_string_generator(4)}'
            current_folder.mkdir(exist_ok=True)
            for idx, cam in enumerate(self.cameras):
                try:
                    filename = f'cam{idx}.jpg'
                    print(f"[CAPTURE] Capturing from camera {idx} ({cam}) to {filename}")
                    cvcam = cv2.VideoCapture(cam)
                    cvcam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                    cvcam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                    success, img = cvcam.read()
                    if not success:
                        print(f"[CAPTURE] FAILED!", file=sys.stderr)
                        return
                    
                    cv2.imwrite(str(current_folder/filename), img)
                    cvcam.release()
                except Exception as excp:
                    traceback.print_exc()
                    return
            self.begin_stream()
            
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