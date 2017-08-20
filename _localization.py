import json
import os
if not os.path.exists(os.path.normpath("plugdata/chat_locales.json")):
    with open(os.path.normpath("plugdata/chat_locales.json"), 'w') as f:
        f.write("{}")

def _get_string(ltext, locale="en"):
    box, strname = ltext.boxname, ltext.strname
    locale_path = os.path.normpath("locale/%s/%s.json" % (box, locale))
    with open(os.path.normpath("locale/%s/en.json" % box)) as f:
        locale = json.load(f)
    if os.path.exists(locale_path):
        with open(locale_path) as f:
            locale.update(json.load(f))
    return locale[strname]


class locale_string:
    def __init__(self, strname, boxname):
        self.strname = strname
        self.boxname = boxname


def get_localized(ltext, uid):
    if isinstance(ltext, locale_string):
        with open(os.path.normpath("plugdata/chat_locales.json")) as f:
            locales = json.load(f)
        if str(uid) in locales:
            return _get_string(ltext, locale=locales[str(uid)])
        else:
            return _get_string(ltext)
    else:
        raise TypeError
