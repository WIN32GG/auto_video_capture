import nextcloud_client
import os
import traceback

from threading import Thread
from pathlib import Path
from time import sleep

class NextCloudSync():

    def __init__(self, folder: Path, nc_token: str) -> None:
        self.sync_folder = folder
        if nc_token is None:
            print("\033[93m[SYNC] Cloud Sync disabled! Provide a sync url\033[0m")
            self.nc = None
        else:
            self.nc = nextcloud_client.Client("https://dvic.devinci.fr/nextcloud/") #! do not use from_public_url bug in lib
            self.nc.anon_login(nc_token)
            self.start()

    def start(self):
        Thread(target = self._sync_target, daemon=True).start()

    def _sync_target(self):
        print("[SYNC] Started sync thread")
        while True:
            try:
                self.run_sync()
            except:
                traceback.print_exc()
            print("[SYNC] Waiting 60 seconds")
            sleep(60)


    def run_sync(self):
        if self.nc is None: return
        print("[SYNC] Running sync")
        local_files = os.listdir(self.sync_folder)
        upload_list = [file for file in local_files if file not in [f.name for f in self.nc.list("/")]]
        print(f"[SYNC] Files to upload: {upload_list}")
        for f in upload_list:
            self.upload_file(self.sync_folder / f)


    def upload_file(self, file: Path) -> bool:
        print(f"[SYNC] Pushing {file}")
        return self.nc.drop_file(str(file))