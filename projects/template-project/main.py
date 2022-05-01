from app.pretalx import Pretalx
from app.helpers import log

"""
Put your custom processes here
"""

if __name__ == "__main__":
    log.info("launching")
    p = Pretalx()
    p.refresh_all()
