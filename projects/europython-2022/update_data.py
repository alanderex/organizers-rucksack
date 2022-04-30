from pathlib import Path
from app.pretalx import Pretalx
from app.config import BASE_CONF

from omegaconf import OmegaConf

this_module = Path(__file__).parent
CONF = OmegaConf.merge(BASE_CONF, OmegaConf.load(this_module / "config.yml"))

a = 44

