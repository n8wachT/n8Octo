"""
OctoBot stuff
"""
from core import constants
from os import getenv
import html
import logging
LOGGER = logging.getLogger("Utils")
NOTAPLUGIN = True


class message:
    """
    Base message class
    """

    def __init__(self,
                 text="",
                 photo=None,
                 file=None,
                 inline_keyboard=None,
                 parse_mode=None,
                 failed=False,
                 voice=None,
                 reply_to_prev_message=True,
                 extra_args={}):
        self.text = text
        self.file = file
        self.failed = failed
        self.photo = photo
        self.voice = voice
        self.inline_keyboard = inline_keyboard
        self.parse_mode = parse_mode
        self.reply_to_prev_message = reply_to_prev_message
        self.extra_args = extra_args
        self.post_init()

    def post_init(self):
        if isinstance(self.photo, str):
            self.photo_as_preview()
        if self.parse_mode == "MARKDOWN":
            LOGGER.warning("Please do NOT use markdown! It breaks too easily!")

    def enable_web_page_preview(self):
        self.extra_args["disable_web_page_preview"] = False

    def photo_as_preview(self):
        LOGGER.debug(getenv("platform", "telegram"))
        if (not self.text == "") and getenv("platform", "telegram") == "telegram":
            LOGGER.debug("Creating image as preview")
            if self.parse_mode is None:
                self.parse_mode = "HTML"
                self.text = f'<a href="{self.photo}">\u00a0</a>{html.escape(self.text)}'
                self.photo = None
                self.enable_web_page_preview()
            elif self.parse_mode == "HTML":
                self.text = f'<a href="{self.photo}">\u00a0</a>{self.text}'
                self.photo = None
                self.enable_web_page_preview()

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
        message.post_init()
        return message


class Command:
    def __init__(self, func, command, description, inline_support, inline_hidden, hidden, required_args, nsfw):
        self.command = command
        self.description = description
        self.inline_support = inline_support
        self.inline_hidden = inline_hidden
        self.hidden = hidden
        self.required_args = required_args
        self.execute = func
        self.nsfw = nsfw


class Plugin:
    """OctoBot plugin base"""

    def __init__(self, name=None):
        self.name = name
        self.commands = []
        self.message_handlers = {}
        self.inline_buttons = {}
        self.update_hooks = []
        self.inline_commands = {}
        self.state = constants.OK

    def command(self,
                command,
                description="Not available",
                inline_supported=True,
                hidden=False,
                required_args=0,
                inline_hidden=False,
                nsfw=False):
        def decorator(func):
            def wrapper(bot, update, user, args):
                if len(args) >= required_args:
                    return func(bot, update, user, args)
                else:
                    return message(text="Not enough arguments!", failed=True)
            self.commands.append(Command(wrapper, command, html.escape(
                description), inline_supported, inline_hidden, hidden, required_args, nsfw))
        LOGGER.debug("Added command \"%s\" to plugin %s", command, self.name)
        return decorator

    def update(self):
        """
        Plugin would catch EVERY update
        """
        def decorator(func):
            self.update_hooks.append(func)
        LOGGER.debug("Added update handler to plugin %s", self.name)
        return decorator

    def message(self, regex: str):
        """
        Pass regex pattern for your function
        """
        def decorator(func):
            self.message_handlers[regex] = func
        LOGGER.debug("Added regex handler \"%s\" to plugin %s",
                     regex, self.name)
        return decorator

    def inline_button(self, callback_name: str):
        """
        Pass the text your callback name starts with
        """
        def decorator(func):
            self.inline_buttons[callback_name] = func
        LOGGER.debug("Added inline button \"%s\" to plugin %s",
                     callback_name, self.name)
        return decorator

    def inline_command(self, inline_command: str):
        def decorator(func):
            if isinstance(inline_command, str):
                command = (inline_command)
            else:
                command = tuple(inline_command)
            self.inline_commands[command] = func
        LOGGER.debug("Added inline command \"%s\" to plugin %s",
                     inline_command, self.name)
        return decorator


class BrokenPlugin(Plugin):
    """
    Plugin which didnt load successfully
    """

    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        self.state = constants.ERROR
