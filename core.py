"""
OctoBot Core
"""
import importlib.util
import traceback
import os.path
from glob import glob
from logging import getLogger
import re
import sys
import core
from core.constants import ERROR, OK
import core.utils as utils
import settings


def create_void(reply):
    def void(*_, **__):
        return reply
    return void


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

    def __init__(self, load_all=True):
        self.logger = getLogger("OctoBot-Core")
        self.myusername = "broken"
        self.plugins = []
        self.disabled = []
        self.platform = "N/A"
        if len(sys.argv) > 1:
            self.logger.info("Loading only %s", sys.argv[-1])
            self.load_plugin(sys.argv[-1])
        else:
            if load_all:
                self.logger.info("Loading all plugins")
                self.load_all_plugins()

    def create_command_handler(self, command, function, minimal_args=0):
        return

    def load_all_plugins(self):
        self.plugins.clear()
        for filename in glob("plugins/*.py"):
            self.load_plugin(filename)
        self.logger.debug("Adding handlers")
        for plugin in self.plugins:
            for command in plugin.commands:
                rargs = command.required_args
                self.create_command_handler(
                    command.command, command.execute, rargs)

    def load_plugin(self, plugpath):
        plugname = os.path.basename(plugpath).split(".py")[0]
        try:
            try:
                spec = importlib.util.spec_from_file_location(
                    plugpath.replace("/", ".").replace("\\", "."), plugpath)
                plugin = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin)
            except Exception as f:
                self.logger.warning(
                    "Plugin %s failed to init. Traceback:", plugname)
                traceback.print_exc()
                self.plugins.append(utils.BrokenPlugin(name=plugpath))
                return False
            else:
                if plugin.plugin.name == None:
                    plugin.plugin.name = plugname
                self.plugins.append(plugin.plugin)
                self.logger.debug("Module %s loaded", plugname)
                return True
        except Exception:
            self.logger.critical(
                "An unknown core error got raised while loading %s. Traceback:", plugname)
            traceback.print_exc()
            return False

    def handle_command(self, update, nsfw_ok=True):
        for plugin in self.plugins:
            incmd = update.message.text.replace("!", "/")
            incmd = incmd.replace("$", "/")
            incmd = incmd.replace("#", "/")
            for command_info in plugin.commands:
                aliases = command_info.command
                function = command_info.execute
                if isinstance(aliases, str):
                    aliases = [aliases]
                for command in aliases:
                    state_only_command = incmd == command or incmd.startswith(
                        command + " ")
                    state_word_swap = len(incmd.split(
                        "/")) > 2 and incmd.startswith(command)
                    state_mention_command = incmd.startswith(
                        command + "@" + self.myusername)
                    if state_only_command or state_word_swap or state_mention_command:
                        if command_info.nsfw and not nsfw_ok:
                            return create_void(core.message(text="This command is only for NSFW channels.", failed=True))
                        return function

    def handle_update(self, update):
        upd_handlers = []
        for plugin in self.plugins:
            for func in plugin.update_hooks:
                upd_handlers.append(func)
        self.logger.debug(upd_handlers)
        return upd_handlers

    def handle_inline(self, update):
        acommands = []
        for plugin in self.plugins:
            for command_info in plugin.commands:
                aliases = command_info.command
                function = command_info.execute
                if isinstance(aliases, str):
                    aliases = [aliases]
                for alias in aliases:
                    if update.inline_query.query == alias or update.inline_query.query.startswith(alias + " "):
                        if command_info.inline_hidden:
                            continue
                        elif command_info.inline_support:
                            acommands.append([function, alias])
                        else:
                            acommands.append([create_void(core.message(
                                "%s command does not support inline mode" % alias)), alias])
                        continue
        return acommands

    def handle_inline_custom(self, update):
        inline_cmds = []
        for plugin in self.plugins:
            for command, func in plugin.inline_commands.items():
                if isinstance(command, str):
                    command = [command]
                for alias in command:
                    if update.inline_query.query.startswith(alias):
                        inline_cmds.append(func)
        return inline_cmds

    def handle_inline_button(self, query):
        for plugin in self.plugins:
            for callback, func in plugin.inline_buttons.items():
                if query.data.startswith(callback):
                    return func

    def handle_message(self, update):
        handlers = []
        for plugin in self.plugins:
            try:
                for regex, func in plugin.message_handlers.items():
                    if re.match(regex, update.message.text):
                        handlers.append(func)
            except TypeError:
                pass
        return handlers
