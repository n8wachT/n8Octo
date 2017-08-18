"""
Octeon stuff
"""
from octeon import constants
import html
NOTAPLUGIN = True


class message:
    """
    Base message class

    Raises:
        TypeError on incompatible conditions, like photo and parse_mode
    """

    def __init__(self,
                 text="",
                 photo=None,
                 file=None,
                 inline_keyboard=None,
                 parse_mode=None,
                 failed=False):
        self.text = text
        self.file = file
        self.failed = failed
        self.photo = photo
        self.inline_keyboard = inline_keyboard
        self.parse_mode = parse_mode
        if photo and file:
            raise TypeError("Send file and photo at same time?!")
        if (photo or file) and parse_mode:
            raise TypeError(
                "parse_mode and photo/file cant be used at same time!")

    @classmethod
    def from_old_format(cls, reply):
        message = cls()
        if isinstance(reply, str):
            message.text = reply
        elif reply is None:
            return
        elif reply[1] == constants.TEXT:
            message.text = reply[0]
        elif reply[1] == constants.MDTEXT:
            message.text = reply[0]
            message.parse_mode = "MARKDOWN"
        elif reply[1] == constants.HTMLTXT:
            message.text = reply[0]
            message.parse_mode = "HTML"
        elif reply[1] == constants.NOTHING:
            pass
        elif reply[1] == constants.PHOTO:
            message.photo = reply[0]
        elif reply[1] == constants.PHOTOWITHINLINEBTN:
            message.photo = reply[0][0]
            message.text = reply[0][1]
            message.inline_keyboard = reply[0][2]
        if "failed" in reply:
            message.failed = True
        return message


class Plugin:
    """Octeon plugin base"""

    def __init__(self):
        self.commands = []
        self.handlers = []
        self.inline_buttons = []

    def command(self,
                command,
                description="Not available",
                inline_supported=True,
                hidden=False,
                required_args=0):
        def decorator(func):
            self.commands.append({
                "command": command,
                "description": html.escape(description),
                "function": func,
                "inline_support": inline_supported,
                "hidden": hidden,
                "required_args": required_args
            })
        return decorator

    def message(self, regex: str):
        """
        Pass regex pattern for your function
        """
        def decorator(func):
            self.handlers.append({
                "regex": regex,
                "function": func,
            })
        return decorator

    def inline_button(self, callback_name: str):
        """
        Pass the text your callback name starts with
        Disclaimer: this may not work in Octeon-Discord
        """
        def decorator(func):
            self.inline_buttons.append({
                "callback": callback_name,
                "function": func,
            })
        return decorator
