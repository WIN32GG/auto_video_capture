#!/bin/env python3
from argparse import ArgumentParser
from auto_camera_capture.capture import CameraCapture
import sys

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--camera", "-c", type=str, nargs="+", action="store", required=True)
    parser.add_argument("--delay", "-d", default=60, type=int, help="Delay in seconds")
    parser.add_argument("--output", "-o", default="./save", help="Storage directory")

    args = parser.parse_args()
    
    print("=-=-=-=-=-=-=-=- Press enter to stop the program =-=-=-=-=-=-=-=-")
    capture = CameraCapture(delay=args.delay, cameras=args.camera, save_base_path=args.output)
    capture.start()

    input()