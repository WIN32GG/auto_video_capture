#!/bin/env python3


try:
    import cv2
except ImportError:
    print("\033[91m\033[1mERROR: Cannot import opencv\033[0m")
    print("\033[93mMake sure opencv is intalled and that you are running the correct python interpreter\033[0m")
    exit(2)

from argparse import ArgumentParser
from auto_camera_capture.capture import CameraCapture
import sys
import time

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--camera", "-c", type=str, nargs="+", action="store", required=True)
    parser.add_argument("--delay", "-d", default=60, type=int, help="Delay in seconds")
    parser.add_argument("--output", "-o", default="./save", help="Storage directory")
    parser.add_argument("--restart", "-r", default=True, help="Restart automatically", action="store_true")
    parser.add_argument("--sync", "-s", required=False, default=None, type=str, nargs='+', action="store", help="Nextcloud shared folder urls")
    parser.add_argument("--show", required=False, default=None, type=str, help="Video to stream")

    args = parser.parse_args()
    
    capture = CameraCapture(delay=args.delay, cameras=args.camera, save_base_path=args.output, nc_sync_urls=args.sync, show=args.show)
    capture.start()
    
    if args.restart:
        print("[SETUP] Auto restart is enabled")
        while True:
            capture.join()
            print("\033[91m\033[1m[WATCHDOG] Error in capture detected. \033[0m")
            print(f"\033[93m[WATCHDOG] Capture thread failure: waiting {args.delay} before restarting\033[0m")
            time.sleep(args.delay)
            capture.start()
    else:
        print("=-=-=-=-=-=-=-=- Press enter to stop the program =-=-=-=-=-=-=-=-")
        input()