import inspect
from pathlib import Path

import omegaconf
from omegaconf import OmegaConf

from app.config import BASE_CONF
from app.helpers import log


class LoadConfig:
    """
    Loads and joins project's and base configs.
    Determines project's config file and project dir by heuristics
    """

    def __init__(self, caller, project_config_path: Path | str | None = None, project_dir: Path | str | None = None):
        """

        :param project_config_path: explicit Path otherwise it will be located following conventions automatically
        :param project_dir: explicit Path or otherwise it will be located following conventions automatically
        """
        log.debug(
            f"launching {self.__class__.__name__} with params",
            project_config_path=f"{project_config_path}",
            project_dir=f"{project_dir}",
        )
        self.caller = caller  # module calling
        log.debug(f"caller is {self.caller}")

        self.project_dir = self._look_for_project_dir(project_dir)
        self.project_config_path: Path | None = None
        project_config_path = self._load_project_config(project_config_path)
        self.config = OmegaConf.merge(BASE_CONF, project_config_path)

    def _load_project_config(self, project_config) -> omegaconf.dictconfig.DictConfig:
        if project_config is None:  # default in __init__
            try:
                project_config = self._look_for_config(self.project_dir)
            except FileNotFoundError:

                raise ValueError("Please provide the Path to the project's config.yml in `project_config`")
        if isinstance(project_config, str):
            project_config = Path(project_config).resolve()
        if not isinstance(project_config, Path) or not project_config.exists():
            raise FileNotFoundError("project's config could not be located")
        log.debug(f"located project's config path at {project_config}")
        self.project_config_path = project_config
        config = OmegaConf.load(project_config)
        return config

    def _look_for_config(self, project_dir) -> Path:
        """checks for the project's configuration file located at project's directory"""
        # convention projects/project_dir/config.yml
        default_config_path = self._look_for_project_dir(project_dir) / "config.yml"
        if default_config_path.exists():
            log.debug(f"located project's config path at {default_config_path}")
            return default_config_path
        msg = (
            "The project's configuration file could not be located, "
            "it should be at the project's directory named 'config.yml'"
        )
        log.debug(msg)
        raise FileNotFoundError(f"{msg}")

    def _look_for_project_dir(self, project_dir) -> Path:
        """helper method to determine the project's directory along the conventions"""
        log.debug(f"locating project_dir {project_dir if project_dir else 'by convention'}")
        if project_dir is None:  # default in __init__
            project_dir = Path(self.caller.filename).parent
        if isinstance(project_dir, str):
            project_dir = Path(project_dir).resolve()
        if not isinstance(project_dir, Path) or not project_dir.exists():
            msg = "project's directory could not be located"
            log.debug(f"{msg}")
            raise NotADirectoryError(f"{msg}")

        while len(project_dir.parts) > 1:
            if project_dir.parent.name == "projects":  # convention projects/project_dir/
                log.debug(f"located projects directory at {project_dir}")
                return project_dir
            project_dir = project_dir.parent
        msg = "the projects directory could not be located, please follow the conventions"
        log.debug(msg)
        raise NotADirectoryError(f"{msg} -  see set-up.")
