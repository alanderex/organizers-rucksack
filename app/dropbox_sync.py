import inspect
from pathlib import Path

import dropbox
from omegaconf import omegaconf

from app.helpers import log
from app.config import BASE_CONF
from app.load_config import LoadConfig

"""
Dropbox interactions
- sync file from directory to local directory
"""


class DropBox:
    def __init__(self, project_config_path: Path | str | None = None, project_dir: Path | str | None = None):

        self.caller = inspect.stack()[1]  # module calling
        config = LoadConfig(self.caller, project_config_path, project_dir)

        self.project_dir = config.project_dir
        self.config: omegaconf.DictConfig = config.config

        self.token = BASE_CONF["dropbox"]["token"]
        self.dbx = dropbox.Dropbox(self.token)
        log.info("logged into dropbox")

        self.dst = Path(self.config.dropbox.video_download).resolve()
        self.dst.mkdir(exist_ok=True, parents=True)
        log.info(f"created download dir {self.dst.parent}/{self.dst.name}")

    def list_dir(self):
        return self.dbx.files_list_folder("/PyConDEPyData2022/EDIT VIDEOS").entries
