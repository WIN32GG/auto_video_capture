import nextcloud_client
import os
import traceback

from threading import Thread
from pathlib import Path
from time import sleep
from six.moves.urllib import parse

SYNC_WAIT_TIME = 30

class NextCloudSync():

    def __init__(self, folder: Path, nc_urls: list[str]) -> None:
        self.sync_folder = folder
        self.ncs: list[nextcloud_client.Client] = []
        if nc_urls is None or len(nc_urls) == 0:
            print("\033[93m[SYNC] Cloud Sync disabled! Provide a sync url\033[0m")
            self.ncs = None
        else:
            for url in nc_urls:
                public_link_components = parse.urlparse(url)
                url = public_link_components.scheme + '://' + public_link_components.hostname + '/'.join(public_link_components.path.split("/")[:-2])
                folder_token = public_link_components.path.split('/')[-1]       
                nc = nextcloud_client.Client(url) #! do not use from_public_url bug in lib
                nc.anon_login(folder_token)
                self.ncs.append(nc)

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
            print(f"[SYNC] Waiting {SYNC_WAIT_TIME} seconds")
            sleep(SYNC_WAIT_TIME)


    def run_sync(self):
        if len(self.ncs) == 0: return
        
        print("[SYNC] Running sync")
        local_files = []
        dd = str(self.sync_folder)
        for w in os.walk(dd):
            if len(w[2]) == 0: continue
            for f in w[2]:
                d = w[0].replace(f'{dd}/', '')
                local_files.append('/'+os.path.join(d, f))
        print(f"[SYNC] Collected local files: {local_files}")
    
        for nc in self.ncs:
            print(f"[SYNC] Running for {nc.url}")
            try:
                rmote = [f.path for f in nc.list('/', depth=2)]
                # print(f"[SYNC] Remote: {rmote}")
                upload_list = [file for file in local_files if file not in rmote]
                print(f"[SYNC] Files to upload: {upload_list}")
                for f in upload_list:
                    if '/' in f:
                        d = f.split('/')[1]
                        d = f'/{d}/'
                        if d not in rmote:
                            print(f"[SYNC] mkdir {d}")
                            nc.mkdir(d)
                            rmote.append(d)
                    self.upload_file(nc, f'{str(self.sync_folder)}{f}', f)
            except:
                traceback.print_exc()


    def upload_file(self, nc: nextcloud_client.Client, file: Path, remote: str) -> bool:
        print(f"[SYNC] Pushing {file}")
        return nc.put_file(remote, str(file))
        return nc.drop_file(str(file))