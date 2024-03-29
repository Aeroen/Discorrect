#!/usr/bin/env python3


"""
    [Discorrect - Message shredder for Discord - by Roen, 2020]
"""


from argparse import ArgumentParser
from atexit import register
from brotli import decompress, error as BrotliError
from copy import copy
from json import dumps, loads
from random import choice, randint, uniform
from re import match
from requests import Session
from string import ascii_letters, digits, punctuation, whitespace
from sys import maxsize
from time import sleep


DEFAULT_USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.20 "
                      "Chrome/91.0.4472.164 Electron/13.6.6 Safari/537.36")


class Discorrect:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        if self.user.isnumeric():
            self.is_numeric_user = True
        elif match(r"^.*#[\d]{4}$", self.user):
            self.is_numeric_user = False
        else:
            raise ValueError("Invalid user name or ID")

        self.sleep_time = {
            0: (3.50, 6.50),    # 5s on average
            1: (2.75, 5.25),    # 4s on average
            2: (2.25, 3.75),    # 3s on average
            3: (1.50, 2.50)     # 2s on average
        }.get(self.speed, (1.50, 2.50)) # anything over 3 is still 3

        self.characters = ascii_letters + digits + punctuation + whitespace
        self.base_url = ("https://discord.com/api/v9/channels/{}/messages"
                         .format(self.channel))
        self.last_ident = self.restore
        self.amount_deleted = 0

        register(self.__exit)
        self.session = Session()
        self.__headers()


    def __str__(self):
        return str(self.__dict__)


    def shred(self):
        while self.max_delete > self.amount_deleted:
            vprint("Retrieving messages... ", end="", flush=True,
                   verbose=self.verbose)
            messages = self.__retrieve()
            vprint("done", verbose=self.verbose)

            parsed = self.__parse(messages)

            if parsed is None:
                break

            for ident, message, attachments in parsed:
                if message:
                    vprint('Message "{}"... '.format(message), end="",
                           flush=True, verbose=self.verbose)

                    if self.dont_overwrite == False:
                        sleep(uniform(*self.sleep_time))
                        self.__overwrite(ident)
                        vprint("overwritten... and ", end="", flush=True,
                               verbose=self.verbose)

                    sleep(uniform(*self.sleep_time))
                    self.__delete(ident)
                    vprint("deleted!", verbose=self.verbose)
                else:
                    sleep(uniform(*self.sleep_time))
                    self.__delete(ident)
                    if attachments:
                        # Only a media, without any text
                        vprint("Media deleted!", verbose=self.verbose)
                    else:
                        # System message, e.g. starting a call or pinning message
                        vprint("System message deleted! (if possible)",
                               verbose=self.verbose)


                if self.amount_deleted >= self.max_delete:
                    break

            print("Current restore point: {}".format(self.last_ident))
            sleep(uniform(*self.sleep_time))


    def __exit(self):
        print("Done: {} messages deleted".format(self.amount_deleted))


    def __headers(self):
        self.get_headers = {
            "authority": "discord.com",                       #  0
            "x-super-properties": self.super_properties,      #  1
            "x-discord-locale": self.language,                #  2
            "authorization": self.token,                      #  3
            "accept-encoding": "gzip, deflate, br",           #  4
            "accept-language": self.language,                 #  5
            "user-agent": self.user_agent,                    #  6
            "content-type": None,                             #  7
            "accept": "*/*",                                  #  8
            "origin": None,                                   #  9
            "sec-fetch-site": "same-origin",                  # 10
            "sec-fetch-mode": "cors",                         # 11
            "sec-fetch-dest": "empty",                        # 12
            "referer": "https://discord.com/channels/@me",    # 13
            "cookie": self.cookies                            # 14
        }

        self.delete_headers = copy(self.get_headers)
        self.delete_headers["origin"] = "https://discord.com"
        self.patch_headers = copy(self.delete_headers)
        self.patch_headers["content-type"] = "application/json"


    def __retrieve(self):
        self.session.headers = self.get_headers
        params = {"before": self.last_ident, "limit": 50}
        req = self.session.get(self.base_url, params=params)

        if req.status_code != 200:
            raise ConnectionError("Could not retrieve any message")

        try:
            return decompress(req.content)
        except BrotliError:
            return req.content


    def __parse(self, messages):
        unserialized = loads(messages)

        if not unserialized: # No more messages
            return None

        self.last_ident = unserialized[-1]["id"]

        if self.is_numeric_user:
            return [(m["id"], m["content"], bool(m["attachments"]))
                    for m in unserialized if m["author"]["id"] == self.user]
        else:
            return [(m["id"], m["content"], bool(m["attachments"]))
                    for m in unserialized
                    if "{}#{}".format(m["author"]["username"],
                                      m["author"]["discriminator"]) == self.user]


    def __overwrite(self, ident):
        payload = dumps({"content": "".join((choice(self.characters)
                                             for _ in range(randint(5, 200))))})
        self.session.headers = self.patch_headers
        req = self.session.patch("{}/{}".format(self.base_url, ident),
                                                data=payload)
        if req.status_code != 200:
            raise ConnectionError("An error occurred while overwriting a message")


    def __delete(self, ident):
        self.session.headers = self.delete_headers
        req = self.session.delete("{}/{}".format(self.base_url, ident))

        if req.status_code not in (204, 403):
            # 403 : can't delete "x started a call"
            raise ConnectionError("An error occurred while deleting a message")

        self.amount_deleted += 1


def vprint(*args, **kwargs):
    if kwargs.pop("verbose") == True:
        print(*args, **kwargs)


if __name__ == "__main__":
    parser = ArgumentParser(description="Message shredder for Discord.")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="increase output verbosity")
    parser.add_argument("-u", "--user", required=True,
                        help="username (name#1234) or user ID")
    parser.add_argument("-t", "--token", required=True,
                        help="Discord token")
    parser.add_argument("-c", "--channel", required=True,
                        help=("ID of the Discord channel you want your "
                              "messages deleted from"))
    parser.add_argument("-r", "--restore", type=int,
                        help="ID of the last message seen (checkpoint)")
    parser.add_argument("-s", "--speed", default=2, type=int,
                        help=("how short the pause between actions is "
                              "(default: 3s on average)"))
    parser.add_argument("-d", "--dont-overwrite", action="store_true",
                        help="don't overwrite before deletion")
    parser.add_argument("-m", "--max-delete", default=maxsize, type=int,
                        help="maximum amount of messages to delete")
    parser.add_argument("--super-properties",
                        help="informations about your system")
    parser.add_argument("--language", default="en-GB",
                        help="language used by Discord")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT,
                        help="Discord user agent")
    parser.add_argument("--cookies",
                        help="cookies (locale, __cfduid, __dcfduid, etc.)")

    args = parser.parse_args()
    dis = Discorrect(**vars(args))
    dis.shred()
