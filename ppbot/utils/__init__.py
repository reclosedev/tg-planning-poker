import re
import sys
from logbook import StreamHandler
from logbook.compat import redirect_logging


def init_logging():
    StreamHandler(sys.stdout).push_application()
    redirect_logging()


def get_valid_filename(s):
    """
    https://github.com/django/django/blob/master/django/utils/text.py

    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)
