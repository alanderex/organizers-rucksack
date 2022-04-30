from pathlib import Path

from omegaconf import OmegaConf, DictConfig

project_root = Path(__file__).resolve().parents[2]
this_module = Path(__file__).parent

BASE_CONF = OmegaConf.load(this_module / "config.yml")

BASE_CONF["pretalx"]["token"] = (
        project_root / BASE_CONF.pretalx.token_dir / BASE_CONF.pretalx.token_file_name
).open().read()
