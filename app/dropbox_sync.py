import inspect
from pathlib import Path

import dropbox
from dropbox.files import FileMetadata, FolderMetadata
from omegaconf import omegaconf

from app.helpers import log
from app.config import BASE_CONF
from app.load_config import LoadConfig

"""
Dropbox interactions
- sync file from directory to local directory

Make sure to create app in 
https://www.dropbox.com/developers/apps
The access token is short lived! but it can be re-generated
For persistent sign in use Oauth2 (not implemented)
"""


class DropBox:
    def __init__(self, project_config_path: Path | str | None = None, project_dir: Path | str | None = None):

        self.caller = inspect.stack()[1]  # module calling
        config = LoadConfig(self.caller, project_config_path, project_dir)

        self.project_dir = config.project_dir
        self.config: omegaconf.DictConfig = config.config

        self.token = BASE_CONF["dropbox"]["token"]

        self.app_key = None
        self.app_secret = None
        # noinspection PyBroadException
        try:
            self.app_key = self.config.dropbox.app_key
            self.app_secret = self.config.dropbox.app_secret
        except Exception as e:
            pass
        if self.app_key and self.app_secret:
            # use oauth2
            self.dbx = dropbox.Dropbox(self.token, app_key=self.app_key, app_secret=self.app_secret)
        else:
            # fallback to token
            self.dbx = dropbox.Dropbox(self.token)

        log.info("logged into dropbox")

        self.dst = Path(self.config.dropbox.video_download).resolve()
        self.dst.mkdir(exist_ok=True, parents=True)
        log.info(f"created download dir {self.dst.parent}/{self.dst.name}")

    def list_dir(self, fldr: str):
        return self.dbx.files_list_folder(fldr).entries

    def download_dir(self, fldr: str, sub_dirs: str = ""):
        to_download = self.list_dir(fldr)
        for element in to_download:
            self.download(element, sub_dirs)

    def download(self, element, sub_dirs: str = ""):
        if isinstance(element, FolderMetadata):
            if sub_dirs:
                sub_dirs = str(Path(sub_dirs) / Path(element.path_lower).name)
            else:
                sub_dirs = str(Path(element.path_lower).name)

            self.download_dir(element.path_lower, sub_dirs)

        if not isinstance(element, FileMetadata):
            return
        if not element.is_downloadable:
            log.warning(f"is not downloadable: {element.path_lower}")

        local_destination = Path(self.config.dropbox.video_download)
        if sub_dirs:
            # handling subdirectories within download scope
            local_destination = local_destination / sub_dirs
        local_destination.mkdir(exist_ok=True, parents=True)
        local_destination = local_destination / f"{Path(element.path_lower).name}"
        if local_destination.exists():
            log.info(f"downloaded already: {element.path_lower}")
            return

        log.info(f"downloading: {element.path_lower}")
        tmp_file = local_destination.with_suffix(f"{local_destination.suffix}.tmp")
        # noinspection PyBroadException
        try:
            self.dbx.files_download_to_file(str(tmp_file.resolve()), element.path_lower)
            tmp_file.rename(local_destination)
            log.info(f"downloaded: {element.path_lower}")
        except ConnectionError:
            log.warning(f"connection error: terminating download: {element.path_lower}")
        except Exception as e:
            log.warning(f"error {e}: terminating download: {element.path_lower}")
        finally:
            tmp_file.unlink(missing_ok=True)

    def oauth2(self):
        try:
            app_key = self.config.dropbox.app_key
            if not app_key:
                raise
        except Exception as e:
            raise ValueError(f"Dropbox app key not set!")

        authorization_url = f"https://www.dropbox.com/oauth2/authorize?client_id={app_key}&response_type=code"

        # send the user to the authorization URL:
        print('Go to the following URL and allow access:')
        print(authorization_url)

        # get the authorization code from the user:
        authorization_code = input('Enter the code:\n')

        # exchange the authorization code for an access token:
        token_url = "https://api.dropboxapi.com/oauth2/token"
        params = {
            "code": authorization_code,
            "grant_type": "authorization_code",
            "client_id": app_key,
            "client_secret": app_secret
        }
        r = requests.post(token_url, data=params)
