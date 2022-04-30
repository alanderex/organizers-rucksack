from pathlib import Path
from app.pretalx import Pretalx
from app.config import BASE_CONF

from omegaconf import OmegaConf

if __name__ == "__main__":
    this_module = Path(__file__).parent
    CONF = OmegaConf.merge(BASE_CONF, OmegaConf.load(this_module / "config.yml"))

    # make sure private dirs exist
    (this_module / BASE_CONF.private_path).resolve().mkdir(exist_ok=True)
    (this_module / BASE_CONF.data_path).resolve().mkdir(exist_ok=True)
    (this_module / BASE_CONF.public_path).resolve().mkdir(exist_ok=True)

    p = Pretalx(CONF, this_module)
    p.refresh_submissions_from_pretalx()
    a = 99
