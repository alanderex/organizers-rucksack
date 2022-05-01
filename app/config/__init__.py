from pathlib import Path

from omegaconf import OmegaConf


project_root = Path(__file__).resolve().parents[2]
this_module = Path(__file__).parent

BASE_CONF = OmegaConf.load(this_module / "config.yml")

BASE_CONF["pretalx"]["token"] = (
    (project_root / BASE_CONF.pretalx.token_dir / BASE_CONF.pretalx.token_file_name).open().read()
)

if BASE_CONF.dropbox:
    dropbox_token = project_root / BASE_CONF.pretalx.token_dir / BASE_CONF.dropbox.token_file_name
    if dropbox_token.exists():
        BASE_CONF["dropbox"]["token"] = dropbox_token.open().read()
