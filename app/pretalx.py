import json
from pathlib import Path
from typing import List

import requests
import omegaconf

from app.config import project_root


class Pretalx:

    def __init__(self, config: omegaconf.dictconfig.DictConfig):
        self.config = config

    @property
    def submissions_url(self):
        return f"{self.config.pretalx.base_url}/api/events/{self.config.pretalx_event_slug}/submissions/"

    @property
    def speakers_url(self):
        return f"{self.config.pretalx.base_url}/api/events/{self.config.pretalx_event_slug}/speakers"

    @property
    def pretalx_headers(self):
        return {
            "Accept": "application/json, text/javascript",
            "Authorization": f"Token {self.config.pretalx.token}",
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

    def get_all_data_from_pretalx(self, url, params=None) -> List:
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

    def refresh_submissions_from_pretalx(self, accepted_only=True):
        """
        Load submissions from pretalx API, store to JSON
        :param accepted_only:
        :return:
        """
        if not accepted_only:
            submissions = self.get_all_data_from_pretalx(self.submissions_url)
        else:
            submissions = self.get_all_data_from_pretalx(self.submissions_url, params={"state": "accepted"})
            submissions.extend(self.get_all_data_from_pretalx(self.submissions_url, params={"state": "confirmed"}))
        self.save_submissions_raw_to_file(submissions)

    @classmethod
    def _to_full_path(cls, path) -> Path:
        return project_root / path

    def save_submissions_to_file(self, submissions):
        with self._to_full_path(self.config.submissions.path).open("w") as f:
            json.dump(submissions, f, indent=4)

    def save_submissions_raw_to_file(self, submissions):
        with self._to_full_path(self.config.submissions.raw_path).open("w") as f:
            json.dump(submissions, f, indent=4)

    def load_submissions_from_file(self):
        with self._to_full_path(self.config.submissions.raw_path).open() as f:
            submissions = json.load(f)
        return submissions

    def load_submissions_raw_from_file(self):
        with self._to_full_path(self.config.submissions.raw_path).open() as f:
            submissions = json.load(f)
        return submissions

    def save_speakers_raw_to_file(self, speakers):
        with self._to_full_path(self.config.speakers.raw_path).open("w") as f:
            json.dump(speakers, f, indent=4)

    def load_speakers_raw_from_file(self):
        with self._to_full_path(self.config.speakers.raw_path).open() as f:
            speakers = json.load(f)
        return speakers

    def save_speaker_to_file(self, submissions):
        with self._to_full_path(self.config.speakers.path).open("w") as f:
            json.dump(submissions, f, indent=4)

    def load_speakers_from_file(self):
        with self._to_full_path(self.config.speakers.path).open() as f:
            speakers = json.load(f)
        return speakers
