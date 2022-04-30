import json
from pathlib import Path

import omegaconf
import requests


class PretalxAPI:
    """
    Interface to provide the URLs and access headers for pretalx.
    """
    def __init__(self, section_name: str, config: omegaconf.dictconfig.DictConfig):
        """

        :param section_name:
        :param config:
        """
        self.__config = config
        self.section_name = section_name
        # self.submissions = self._url_constructor("submissions")
        # self.speakers = self._url_constructor("speakers")
        # self.questions = self._url_constructor("questions")
        # self.answers = self._url_constructor("answers")

    def _url_constructor(self, ep):
        return f"{self.__config.pretalx.base_url}/api/events/{self.__config.pretalx_event_slug}/{ep}/"

    @property
    def url(self):
        return self._url_constructor(self.section_name)

    @property
    def pretalx_headers(self):
        return {
            "Accept": "application/json, text/javascript",
            "Authorization": f"Token {self.__config.pretalx.token}",
        }

    def get_from_pretalx_api(self, url: str, params: dict | None = None):
        """
        Helper function to get data from Pretalx API
        :param url: URL to call
        :param params: optional filters
        :return: results and next url (if any)
        """
        if not params:
            params = {}
        res = requests.get(url, headers=self.pretalx_headers, params=params)
        res_json = res.json()
        return res_json["results"], res_json["next"]

    def get_all_data_from_pretalx(self, url, params=None) -> list:
        """
        Helper to get paginated data from Pretalx API
        :param url: url to start from
        :param params: optional filters

        """
        api_result = []
        while url:
            chunk, url = self.get_from_pretalx_api(url, params=params)
            api_result.extend(chunk)
        return api_result


class Section:
    """
    Handle API sections, i.e. submissions, speakers,…
    """
    def __init__(self, section_name: str, config: omegaconf.dictconfig.DictConfig, project_root: Path):
        """

        :param section_name: name of the section, must be in config
        :param config: config node for section
        :param project_root:
        """
        self.config = config[section_name]
        self.project_root = project_root
        self._data = []

        self.api = PretalxAPI(section_name, config)

    def load(self):
        with self._to_full_path(self.config.raw_path).open("w") as f:
            self.data = json.load(f)

    def save_to_json(self):
        with self._to_full_path(self.config.raw_path).open("w") as f:
            json.dump(self.data, f, indent=4)

    def refresh(self):
        self.data = self.api.get_all_data_from_pretalx(self.api.url)
        self.save_to_json()

    def _to_full_path(self, fpath) -> Path:
        """ helper returning a full Path to the file """
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
            except FileNotFoundError:
                self.refresh()
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    @property
    def init(self):
        return self


class Pretalx:

    def __init__(self, config: omegaconf.dictconfig.DictConfig, project_root: Path):
        self.config = config
        self.project_root = project_root
        self._create_working_dirs()

        self._speaker_raw = []
        self._submissions_raw = []

        self.sections = [k for k, v in self.config.items()
                         if isinstance(v, omegaconf.DictConfig) and v.get("api_section")]

        # stub
        self.speakers: Section | None = None
        self.submissions: Section | None = None
        self.schedule: Section | None = None
        self.answers: Section | None = None
        self.questions: Section | None = None

        for section in self.sections:
            setattr(self, section, Section(section, self.config, project_root).init)

    def _create_working_dirs(self):
        """
        Creates working dirs in project
        :return: None
        """
        self.private_path = (self.project_root / self.config.private_path).resolve()
        self.private_path.mkdir(exist_ok=True)
        self.data_path = (self.project_root / self.config.data_path).resolve()
        self.data_path.mkdir(exist_ok=True)
        self.public_path = (self.project_root / self.config.public_path).resolve()
        self.public_path.mkdir(exist_ok=True)

    def _to_full_path(self, fpath) -> Path:
        """ helper returning a full Path to the file """
        return self.project_root / fpath

    def save_track_names_to_file(self):
        with self._to_full_path(self.data_path / "track_names.txt").open("w") as f:
            f.write("\n".join(self.track_names))

    def save_submission_states_to_file(self):
        with self._to_full_path(self.data_path / "submission_states.txt").open("w") as f:
            f.write("\n".join(self.submission_states))

    def save_submission_types_to_file(self):
        with self._to_full_path(self.data_path / "submission_types.txt").open("w") as f:
            f.write("\n".join(self.submission_types))

    def refresh_all(self):
        """
        Load all data from pretalx
        Save value lists to file as well for orientation
        :return:
        """
        self.speakers.refresh()
        self.submissions.refresh()
        self.answers.refresh()
        self.questions.refresh()
        self.save_track_names_to_file()
        self.save_submission_states_to_file()
        self.save_submission_types_to_file()

    @property
    def track_names(self) -> list:
        """ list of all tracks present in submissions (does not cover all options) """
        tracks = sorted({x["track"][self.config.pretalx.language] for x in self.submissions.data})
        return tracks

    @property
    def submission_states(self) -> list:
        """ list of all states present in submissions (does not cover all options) """
        states = sorted({x["state"] for x in self.submissions.data})
        return states

    @property
    def submission_types(self) -> list:
        """ list of all submission types present in submissions (does not cover all options) """
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
        return [x for x in self.submissions.data if x["state"] in self.config.pretalx.confirmed_accepted]
