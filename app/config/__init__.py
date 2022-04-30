from pathlib import Path

from omegaconf import OmegaConf

project_root = Path(__file__).resolve().parents[2]
this_module = Path(__file__).parent

BASE_CONF = OmegaConf.load(this_module / "config.yml")

# make sure private dirs exist
(project_root / BASE_CONF.private_path).resolve().mkdir(exist_ok=True)
(project_root / BASE_CONF.data_path).resolve().mkdir(exist_ok=True)
(project_root / BASE_CONF.public_path).resolve().mkdir(exist_ok=True)

BASE_CONF["pretalx"]["token"] = (
        project_root / BASE_CONF.pretalx.token_dir / BASE_CONF.pretalx.token_file_name
).open().read()
