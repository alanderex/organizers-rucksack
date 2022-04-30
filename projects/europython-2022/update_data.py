from pathlib import Path
from app.pretalx import Pretalx
from app.config import BASE_CONF

from omegaconf import OmegaConf

if __name__ == "__main__":
    this_module = Path(__file__).parent
    CONF = OmegaConf.merge(BASE_CONF, OmegaConf.load(this_module / "config.yml"))
    p = Pretalx(CONF)
    p.refresh_submissions_from_pretalx()
    a = 99
