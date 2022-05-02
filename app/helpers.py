import logging
import re
from unicodedata import normalize

import structlog

from app.config import BASE_CONF

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt=BASE_CONF.logger.time_fmt, utc=BASE_CONF.logger.use_utc),
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False,
)
log = structlog.get_logger()


def slugify(text, delim="-"):
    """Generates a slightly worse ASCII-only slug."""

    _punctuation_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.:]+')
    _regex = re.compile(r"[^a-z\d]")
    # First parameter is the replacement, second parameter is your input string

    result = []
    for word in _punctuation_re.split(text.lower()):
        word = normalize("NFKD", word).encode("ascii", "ignore")
        word = word.decode("ascii")
        word = _regex.sub("", word)
        if word:
            result.append(word)
    slug = delim.join(result)
    return str(slug)