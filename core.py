"""
OctoBot Core
"""
import importlib.util
import os.path
from glob import glob
from logging import getLogger
import re

import core
from core.constants import ERROR, OK
import settings


class DefaultPlugin:

    def coreplug_reload(self, bot, update, user, *__):
        if user.id == settings.ADMIN:
            self.logger.info("Reload requested.")
            update.message.reply_text("Reloading modules. ")
            self.load_all_plugins()
            return self.coreplug_list()
        else:
            return core.message("Access Denied.")



class OctoBotCore(DefaultPlugin):

    def __init__(self):
        self.logger = getLogger("OctoBot-Core")
        self.myusername = "broken"
        self.plugins = []
        self.disabled = []
        self.platform = "N/A"
        self.logger.info("Starting OctoBot-Core. Loading plugins.")
        self.load_all_plugins()

    def create_command_handler(self, command, function, minimal_args=0):
        return

    def load_all_plugins(self):
        self.plugins.clear()
        for filename in glob("plugins/*.py"):
            self.load_plugin(filename)
        # self.plugins.append({
        #     "state": OK,
        #     "name": "OctoBot Core Plugin",
        #     "commands": [{"command": "/start", "function": self.coreplug_start},
        #                  {"command": "//plugins", "function": self.coreplug_list},
        #                  {"command": "/help", "function": self.coreplug_help},
        #                  {"command": "//reload", "function": self.coreplug_reload},
        #                  {"command": "//pluginload", "function": self.coreplug_load}],
        #     "messagehandles": [],
        #     "disabledin": []
        # })
        self.logger.debug("Adding handlers")
        for plugin in self.plugins:
            for command in plugin["commands"]:
                if "required_args" in command:
                    rargs = command["required_args"]
                else:
                    rargs = 0
                self.create_command_handler(
                    command["command"], command["function"], rargs)

    def load_plugin(self, plugpath):
        plugname = os.path.basename(plugpath).split(".py")[0]
        try:
            spec = importlib.util.spec_from_file_location(
                "core.plugin", plugpath)
            plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin)
        except Exception as f:
            self.logger.warning(
                "Plugin %s failed to init cause of %s", plugname, f)
            self.plugins.append({
                "state": ERROR,
                "name": plugname,
                "commands": [],
                "messagehandles": [],
                "inline_buttons": [],
                "disabledin": []
            })
        else:
            try:
                plugin.PLUGINVERSION
            except AttributeError:
                # Working with outdated plugins.
                self.plugins.append({
                    "state": OK,
                    "name": plugname,
                    "commands": plugin.COMMANDS,
                    "messagehandles": [],
                    "inline_buttons": [],
                    "disabledin": []
                })
                self.logger.debug("Legacy module %s loaded", plugname)
            else:
                # Working with new plugins
                self.plugins.append({
                    "state": OK,
                    "name": plugin.plugin.name if plugin.plugin.name else plugname,
                    "ai": plugin.plugin.ai_events,
                    "commands": plugin.plugin.commands,
                    "messagehandles": plugin.plugin.handlers,
                    "inline_buttons": plugin.plugin.inline_buttons,
                    "disabledin": [],
                    "update_handlers":plugin.plugin.update_hooks
                })
                self.logger.debug("Module %s loaded", plugname)

    def handle_command(self, update):
        for plugin in self.plugins:
            if update.message.chat.id in plugin["disabledin"]:
                continue
            else:
                for command_info in plugin["commands"]:
                    aliases = command_info["command"]
                    function = command_info["function"]
                    if isinstance(aliases, str):
                        aliases = [aliases]
                    for command in aliases:
                        state_only_command = update.message.text == command or update.message.text.startswith(
                            command + " ")
                        state_word_swap = len(update.message.text.split(
                            "/")) > 2 and update.message.text.startswith(command)
                        state_mention_command = update.message.text.startswith(
                            command + "@" + self.myusername)
                        if state_only_command or state_word_swap or state_mention_command:
                            return function

    def handle_update(self, update):
        upd_handlers = []
        for plugin in self.plugins:
            if "update_handlers" in plugin:
                for func in plugin["update_handlers"]:
                    upd_handlers.append(func)
        self.logger.debug(upd_handlers)
        return upd_handlers

    def handle_inline(self, update):
        for plugin in self.plugins:
            for command_info in plugin["commands"]:
                command = command_info["command"]
                function = command_info["function"]
                if update.inline_query.query.startswith(command):
                    return function, command

    def handle_inline_button(self, query):
        for plugin in self.plugins:
            if "inline_buttons" in plugin:
                for command_info in plugin["inline_buttons"]:
                    command = command_info["callback"]
                    function = command_info["function"]
                    if query.data.startswith(command):
                        return function

    def handle_ai(self, update, event):
        for plugin in self.plugins:
            if update.message.chat.id in plugin["disabledin"]:
                continue
            else:
                if "ai" in plugin:
                    for ai_event in plugin["ai"]:
                        event_ = ai_event["action"]
                        function = ai_event["function"]
                        if event == event_:
                            return function

    def handle_message(self, update):
        handlers = []
        for plugin in self.plugins:
            try:
                if "messagehandles" in plugin:
                    for message_info in plugin["messagehandles"]:
                        if re.match(message_info["regex"], update.message.text):
                            handlers.append(message_info["function"])
            except TypeError:
                pass
        return handlers
