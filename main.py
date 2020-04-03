# Nanoy Telegram Bot - It's only me speaking
# Copyright (C) 2020 Yoann Pietri

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Nanoy Telegram Bot.
Usage:
  main.py (start|stop|restart)
  main.py exec
  main.py debug
  main.py (-h | --help)
  main.py --version
Options:
  start         Start the daemon
  stop          Stop the daemon
  restart       Restart the daemon
  exec          Laucnh bot in blocking mode
  debug         Launch bot in blocking mode with debug info
  -h --help     Show this screen.
  --version     Show version.
"""

import configparser
import json
import logging
import os
import re
import requests
import sys
import random
import time

import telegram
from docopt import docopt
from telegram.ext import CommandHandler, Updater, Filters, MessageHandler

from variables import *

try:
    from local_variables import *
except:
    pass


class Bot:
    """"
    Define a wrapper for nanoy-telegram-bot. Defines handlers for commands.
    """

    def __init__(self, directory=None):
        """Initilise the bot
        
        Args:
            directory (string, optional): Where to find list.json and config.ini files. Defaults to None.
        """
        if directory:
            self.directory = directory
        else:
            self.directory = os.path.dirname(os.path.realpath(__file__))

        self.load_config()

        try:
            self.updater = Updater(token=self.token, use_context=True)
            logging.info("Bot {} grabbed.".format(self.updater.bot.username))
        except:
            logging.error("Unable to grab bot.")
            sys.exit()

        self.dispatcher = self.updater.dispatcher

        self.start_handler = CommandHandler("start", self.nanoy)
        self.nanoy_handler = CommandHandler("nanoy", self.nanoy)
        self.jmentape_handler = CommandHandler("jmentape", self.jmentape)
        self.help_handler = CommandHandler("help", self.help)
        self.react_handler = MessageHandler(Filters.text, self.react_to_message)

        self.dispatcher.add_handler(self.start_handler)
        self.dispatcher.add_handler(self.nanoy_handler)
        self.dispatcher.add_handler(self.jmentape_handler)
        self.dispatcher.add_handler(self.help_handler)
        self.dispatcher.add_handler(self.react_handler)

        self.last_message = int(time.time())

    def load_config(self):
        """Load configuration file. The configuration file is the config.ini file in code directory.
        """
        config = configparser.ConfigParser()
        try:
            config.read("{}/config.ini".format(self.directory))
        except Exception as e:
            logging.error("Unable to read config : {}".format(str(e)))
            sys.exit()
        try:
            self.token = config.get("Global", "token")
        except:
            logging.error("Unable to find 'token' parameter in section 'Global'.")
            sys.exit()
        try:
            self.chats = [
                int(chat) for chat in config.get("Global", "chats").split(",")
            ]
        except:
            logging.error("Unable to find 'chats' paraneter in section 'Global'.")
            sys.exit()
        try:
            self.rate = config.getfloat("Global", "rate")
        except:
            logging.error("Unable to find 'rate' parameter in section 'Global'.")
            sys.exit()

        try:
            self.use_dictionnary = config.getboolean("Global", "use_dictionnary")
        except:
            logging.warning("No use_dictionnary setting")
            self.use_dictionnary = True

        try:
            with open("{}/nanoybot_words.txt".format(self.directory), "r") as f:
                self.allowed_words = f.read().splitlines()
        except:
            logging.warning("Unable to load words")
            self.allowed_words = []

        logging.info("Configuration loaded")

    def nanoy(self, update, context):
        """nanoy command handler.
        This command send a random choice from REPLIES.
        
        Args:
            update (dict): message that triggered the handler
            context (CallbackContext): context
        """
        chat_id = update.effective_chat.id
        if chat_id in self.chats:
            context.bot.send_message(chat_id=chat_id, text=random.choice(REPLIES))

    def react_to_message(self, update, context):
        """ract to message command handler.
        This command react to some messages.
        
        Args:
            update (dict): message that triggered the handler
            context (CallbackContext): context
        """
        chat_id = update.effective_chat.id
        if chat_id in self.chats:
            message = update.message.text.lower()
            for arch in ARCH:
                if arch in message:
                    context.bot.send_message(
                        chat_id=chat_id, text="Tu devrais passer à Arch Linux (rip la synchro contacts/agenda par contre)."
                    )
            for key, e in MAP.items():
                if message == key and int(time.time()) - self.last_message > self.rate:
                    self.last_message = int(time.time())
                    context.bot.send_message(chat_id=chat_id, text=random.choice(e))
            react = None
            for word in message.split(" "):
                react = None
                if word[:2] == "dy" and (
                    not self.use_dictionnary or word in self.allowed_words
                ):
                    react = word[2:] or None
                elif word[:2] == "di" and (
                    not self.use_dictionnary or word in self.allowed_words
                ):
                    react = word[2:] or None
                if react and not react == "t":
                    context.bot.send_message(chat_id=chat_id, text=react)

    def jmentape(self, update, context):
        """jmentape command handler.
        This command query jmentape.fr and send response.
        
        Args:
            update (dict): message that triggered the handler
            context (CallbackContext): context
        """
        chat_id = update.effective_chat.id
        if chat_id in self.chats:
            regex = re.compile('<meta property="og:title" content="([^"]*)">')
            i = 0
            match = regex.search("")
            while match is None and i < 10:
                r = requests.get("https://jmentape.fr")
                match = regex.search(r.text)
                i += 1
            jmentape = match.groups()[0]
            context.bot.send_message(chat_id=chat_id, text=jmentape)

    def help(self, update, context):
        """help command handler.
        
        Args:
            update (dict): message that triggered the handler
            context (CallbackContext): context
        """
        chat_id = update.effective_chat.id
        if chat_id in self.chats:
            context.bot.send_message(
                chat_id=chat_id, text="Hi. I'm nanoy bot. Just talking nonsense."
            )
        else:
            context.bot.send_message(
                chat_id=chat_id,
                text="Bot will not work on this chan. You need to add the following chat id : {} to the chats list in config.ini file.".format(
                    chat_id
                ),
            )

    def start_bot(self):
        """Start the bot.
        """
        self.updater.start_polling()


if __name__ == "__main__":
    arguments = docopt(__doc__, version="Nanoy Telegram Bot 0.9")
    daemon = arguments["start"] or arguments["stop"] or arguments["restart"]
    debug = arguments["debug"]

    if debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logfile = os.path.join(os.getcwd(), "nanoy-telegram-bot.log")
        logging.basicConfig(filename=logfile, level=logging.WARNING)

    d = None

    if daemon:
        from daemons.prefab import run

        class ListBotDaemon(run.RunDaemon):
            def __init__(self, directory, *args, **kwargs):
                """Initialise the daemon
                
                Args:
                    directory (string): directory to pass to the bot
                """
                self.directory = directory
                super().__init__(*args, **kwargs)

            def run(self):
                """Run method (called when daemon starts).
                """
                bot = Bot(self.directory)
                bot.start_bot()

        pidfile = "/tmp/nanoy-telegram-bot.pid"
        d = ListBotDaemon(os.path.dirname(os.path.realpath(__file__)), pidfile=pidfile)

    if arguments["start"]:
        d.start()
    elif arguments["stop"]:
        d.stop()
    elif arguments["restart"]:
        d.restart()
    else:
        bot = Bot()
        bot.start_bot()
