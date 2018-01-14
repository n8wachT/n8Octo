import json
import logging
import os
LOGGER = logging.getLogger("OctoBot-Locale")
class LocaleError(Exception):
    pass

class InvalidLocale(LocaleError):
    pass

def convert_loc(path):
    with open(os.path.normpath(path), encoding="utf-8") as f:
        data = f.read().split("---")[1:]
        if data == []:
            raise InvalidLocale("Invalid Locale file. Doesnt contain any strings")
        readed = {}
        for lstring in data:
            try:
                readed[lstring.split("\n")[0].strip()] = "\n".join(lstring.split("\n")[1:]).strip("\n").replace('\\n','\n')
            except RuntimeError:
                readed[lstring.split("\n")[0].strip()] = "\n".join(lstring.split("\n")[1:]).strip("\n")
        return readed

def get_strings(box):
    return convert_loc(os.path.normpath("locale/%s/en.locale" % box)).keys()

def get_locales_dict(box):
    strings = get_strings(box)
    d = {}
    for string in strings:
        d[string] = locale_string(string, box)
    return d

if not os.path.exists(os.path.normpath("plugdata/chat_locales.json")):
    with open(os.path.normpath("plugdata/chat_locales.json"), 'w') as f:
        f.write("{}")

def _get_string(ltext, locale="en"):
    box, strname = ltext.boxname, ltext.strname
    locale_path = os.path.normpath("locale/%s/%s.locale" % (box, locale))
    locale = convert_loc("locale/%s/%s.locale" % (box, "en"))
    if os.path.exists(locale_path):
        locale.update(convert_loc(locale_path))
    return locale[strname]


class locale_string:
    def __init__(self, strname, boxname):
        self.strname = strname
        self.boxname = boxname # BAWX

    def replace(*_, **__):
        raise RuntimeError


def get_localized(ltext, uid):
    if isinstance(ltext, locale_string):
        with open(os.path.normpath("plugdata/chat_locales.json")) as f:
            locales = json.load(f)
        if str(uid) in locales:
            return _get_string(ltext, locale=locales[str(uid)])
        else:
            return _get_string(ltext)
    elif isinstance(ltext, str):
        return ltext
    else:
        raise TypeError
