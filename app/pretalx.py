import inspect
import json
from json import JSONDecodeError
from pathlib import Path

import omegaconf
import requests
import yaml
from omegaconf import OmegaConf

from app.config import BASE_CONF
from app.helpers import log


class PretalxAPI:
    """
    Interface to provide the URLs and access headers for pretalx.
    """

    def __init__(self, section_name: str, project_config: omegaconf.dictconfig.DictConfig):
        """

        :param section_name: API section, e.g. submissions
        :param project_config: config loaded as in Pretalx class
        """
        log.debug(f"launching {self.__class__.__name__} with param", section_name=section_name)
        self.config = project_config
        self.section_name = section_name
        log.debug(f"loaded config for {self.section_name} in {self.__class__.__name__}")

    def _url_constructor(self, ep):
        return f"{self.config.pretalx.base_url}/api/events/{self.config.pretalx_event_slug}/{ep}/"

    @property
    def url(self):
        return self._url_constructor(self.config[self.section_name].endpoint)

    @property
    def pretalx_headers(self):
        return {
            "Accept": "application/json, text/javascript",
            "Authorization": f"Token {self.config.pretalx.token}",
        }

    def get_from_pretalx_api(self, url: str, params: dict | None = None, call_no: int = None):
        """
        Helper function to get data from Pretalx API
        :param url: URL to call
        :param params: optional filters
        :param call_no: optional call no. just for debugging log
        :return: results and next url (if any)
        """
        params = {} if not params else params
        log.debug(f"loading {self.section_name}{'' if call_no is None else f' #' + str(call_no)} data from pretalx API with params", **params)
        if not params:
            params = {}
        res = requests.get(url, headers=self.pretalx_headers, params=params)
        res_json = res.json()
        log.debug(f"loaded {self.section_name}{'' if call_no is None else f' #' + str(call_no)} data from pretalx API with params", **params)
        return res_json["results"], res_json["next"]

    def get_all_data_from_pretalx(self, url, params=None) -> list:
        """
        Helper to get paginated data from Pretalx API
        :param url: url to start from
        :param params: optional filters

        """
        params = {} if not params else params
        log.debug(f"loading {self.section_name} data from pretalx API with params", **params)
        api_result = []
        call_no = 1
        while url:
            chunk, url = self.get_from_pretalx_api(url, params=params, call_no=call_no)
            api_result.extend(chunk)
            call_no += 1
        log.debug(f"loaded all {self.section_name} from pretalx API with params", **params)
        return api_result


class Section:
    """
    Handle API sections, i.e. submissions, speakers,…
    """

    def __init__(self, section_name: str, config: omegaconf.dictconfig.DictConfig, project_dir: Path):
        """

        :param section_name: name of the section, must be in config
        :param config: config node for section
        :param project_dir:
        """
        self.config = config[section_name]
        self.project_root = project_dir
        self._data = []

        self.api = PretalxAPI(section_name, config)

    def load(self):
        with self._to_full_path(self.config.raw_path).open("r") as f:
            self.data = json.load(f)

    def save_to_json(self):
        with self._to_full_path(self.config.raw_path).open("w") as f:
            json.dump(self._data, f, indent=4)

    def refresh(self):
        self._data = self.api.get_all_data_from_pretalx(self.api.url)
        if self._data:  # do not use setter here, might result in endless recursion
            self.save_to_json()

    def _to_full_path(self, fpath) -> Path:
        """helper returning a full Path to the file"""
        return self.project_root / fpath

    @property
    def data(self):
        """
        Return data, if not in RAM load from file, fallback to load from API
        :return:
        """
        if not self._data:
            try:
                self.load()
            except (FileNotFoundError, JSONDecodeError):
                self.refresh()
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def init(self):
        return self


class Pretalx:
    def __init__(self, project_config_path: Path | str | None = None, project_dir: Path | str | None = None):
        """

        :param project_config_path: explicit Path otherwise it will be located following conventions automatically
        :param project_dir: explicit Path or otherwise it will be located following conventions automatically
        """
        log.debug(
            f"launching {self.__class__.__name__} with params",
            project_config_path=f"{project_config_path}",
            project_dir=f"{project_dir}",
        )
        self.caller = inspect.stack()[1]  # module calling
        log.debug(f"caller is {self.caller}")

        self.project_dir = self._look_for_project_dir(project_dir)
        self.project_config_path: Path | None = None
        project_config_path = self._load_project_config(project_config_path)
        self.config = OmegaConf.merge(BASE_CONF, project_config_path)

        self._create_working_dirs()

        self._speaker_raw = []
        self._submissions_raw = []

        self.api_sections = [
            k for k, v in self.config.items() if isinstance(v, omegaconf.DictConfig) and v.get("api_section")
        ]

        # stub
        self.speakers: Section | None = None
        self.submissions: Section | None = None
        self.schedule: Section | None = None
        self.answers: Section | None = None
        self.questions: Section | None = None

        for section in self.api_sections:
            setattr(self, section, Section(section, self.config, self.project_dir).init)

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

    def _create_working_dirs(self):
        """
        Creates working dirs in project
        :return: None
        """
        log.debug(f"set-up: creating working directories")
        self.private_path = (self.project_dir / self.config.private_path).resolve()
        self.private_path.mkdir(exist_ok=True)
        self.data_path = (self.project_dir / self.config.data_path).resolve()
        self.data_path.mkdir(exist_ok=True)
        self.public_path = (self.project_dir / self.config.public_path).resolve()
        self.public_path.mkdir(exist_ok=True)

    def _to_full_path(self, fpath) -> Path:
        """helper returning a full Path to the file"""
        return self.project_dir / fpath

    def save_track_names_to_file(self):
        with self._to_full_path(self.data_path / "track_names.txt").open("w") as f:
            f.write("\n".join(self.track_names))

    def save_submission_states_to_file(self):
        with self._to_full_path(self.data_path / "submission_states.txt").open("w") as f:
            f.write("\n".join(self.submission_states))

    def save_submission_types_to_file(self):
        with self._to_full_path(self.data_path / "submission_types.txt").open("w") as f:
            f.write("\n".join(self.submission_types))

    def save_questions_to_yaml(self):
        """
        Write questions to a yaml file for readability
        Nodes selected are opt-in in project config.yml:
            pretalx.questions.select_nodes
        :return:
        """

        to_yaml = []
        for entry in self.questions.data:
            new_dict = {}
            for node in self.config.pretalx.questions.select_nodes:
                new_dict[node] = self.get_from_lang_tag(entry[node])
            to_yaml.append(new_dict)

        with self._to_full_path(self.data_path / "questions.yml").open("w") as f:
            yaml.dump({x["question"]: x for x in to_yaml}, f)

    def get_from_lang_tag(self, value):
        try:
            if isinstance(value, list):
                if value:
                    value = [self.get_from_lang_tag(x) for x in value]
            elif isinstance(value, dict):
                if value:
                    for k, v in value.items():
                        if k == self.config.pretalx.language:
                            return v
                    value = {k: self.get_from_lang_tag(v) for k, v in value.items()}
            else:
                value = value[self.config.pretalx.language]
        except (KeyError, TypeError, AttributeError):
            pass
        return value

    def refresh_all(self):
        """
        Load all data from pretalx
        Save value lists to file as well for orientation
        :return:
        """
        for section in self.api_sections:
            getattr(self, section).refresh()

        self.save_track_names_to_file()
        self.save_submission_states_to_file()
        self.save_submission_types_to_file()
        self.save_questions_to_yaml()

    @property
    def track_names(self) -> list:
        """list of all tracks present in submissions (does not cover all options)"""
        tracks = sorted({x["track"][self.config.pretalx.language] for x in self.submissions.data})
        return tracks

    @property
    def submission_states(self) -> list:
        """list of all states present in submissions (does not cover all options)"""
        states = sorted({x["state"] for x in self.submissions.data})
        return states

    @property
    def submission_types(self) -> list:
        """list of all submission types present in submissions (does not cover all options)"""
        states = sorted({x["submission_type"][self.config.pretalx.language] for x in self.submissions.data})
        return states

    @property
    def accepted_or_confirmed(self):
        return self._filter_state(self.config.pretalx.confirmed_accepted)

    @property
    def accepted(self):
        return self._filter_state(self.config.pretalx.accepted)

    @property
    def confirmed(self):
        return self._filter_state(self.config.pretalx.confirmed)

    def _filter_state(self, state):
        return [x for x in self.submissions.data if x[state] in self.config.pretalx.confirmed_accepted]
