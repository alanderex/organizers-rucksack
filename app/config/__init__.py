from pathlib import Path

from omegaconf import OmegaConf

project_root = Path(__file__).resolve().parents[2]
token_path = project_root / "_private/TOKEN.txt"

PRETALX_TOKEN = token_path.open().read()


this_module = Path(__file__).parent
BASE_CONF = OmegaConf.load(this_module / "config.yml")

BASE_CONF["pretalx"]["token"] = PRETALX_TOKEN

submissions_path = project_root / Path("_data/submissions.json")
submissions_raw_path = project_root / Path("_data/submissions_raw.json")
speakers_raw_path = project_root / Path("_data/speakers_raw.json")
speakers_path = project_root / Path("_data/speakers.json")

clean_submissions_f = project_root / Path(
    "projects/databags/submissions.json"
)  # filepath

schedule__path = project_root / Path(
    "website/databags/schedule_databag.json"
)  # may be added later
