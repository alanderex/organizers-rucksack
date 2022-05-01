from app.pretalx import Pretalx
from app.helpers import log


if __name__ == "__main__":
    log.info("launching")
    p = Pretalx()
    p.refresh_all()
    # p.save_questions_to_yaml()
    a = 99
