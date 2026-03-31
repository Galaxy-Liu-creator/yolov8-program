import validators
from markupsafe import escape
from validators import validator


def str_escape(s):
    if not s:
        return None
    return str(escape(s))


between = validators.between
domain = validators.domain
email = validators.email
ipv4 = validators.ipv4
ipv6 = validators.ipv6
url = validators.url
uuid = validators.uuid


@validator
def even(value):
    return not (value % 2)
