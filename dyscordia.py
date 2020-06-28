#!/usr/bin/env python3


"""
    [Dyscordia - Message shredder for Discord - by Roen, 2020]
"""


import string

from argparse import ArgumentParser
from copy import deepcopy
from json import dumps, loads
from random import choice, randint, uniform
from re import match
from requests import Request, Session
from sys import maxsize
from time import sleep


DISCORD_BASE_URL = "https://discordapp.com/api/v6/channels/"
DEFAULT_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " \
                     "(KHTML, like Gecko) discord/0.0.10 Chrome/78.0.3904.130 " \
                     "Electron/7.1.11 Safari/537.36"
RAND_MIN, RAND_MAX = 0.5, 1.5 # Should sleep for 1s on average


class Dyscordia:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        if self.user.isnumeric():
            self.is_numeric_user = True
        elif match(r"^.*#[\d]{4}$", self.user):
            self.is_numeric_user = False
        else:
            raise ValueError("Invalid user name or ID")

        self.characters = string.ascii_letters + string.digits + \
                          string.punctuation + string.whitespace
        self.base_url = "{}{}/messages".format(DISCORD_BASE_URL, self.channel)
        self.last_ident = self.restore
        self.amount_deleted = 0

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

            for ident, message in parsed:
                if message:
                    vprint('Message "{}"... '.format(message), end="",
                           flush=True, verbose=self.verbose)
                    sleep(uniform(RAND_MIN, RAND_MAX))
                    self.__overwrite(ident)
                    vprint("overwritten... ", end="", flush=True,
                           verbose=self.verbose)
                    sleep(uniform(RAND_MIN, RAND_MAX))
                    self.__delete(ident)
                    vprint("and deleted!", verbose=self.verbose)
                else: # Only a media, no text
                    sleep(uniform(RAND_MIN, RAND_MAX))
                    self.__delete(ident)
                    vprint("Media deleted!", verbose=self.verbose)

                if self.amount_deleted >= self.max_delete:
                    break

            print("Current restore point: {}".format(self.last_ident))
            sleep(uniform(RAND_MIN, RAND_MAX))

        print("Done: {} messages deleted".format(self.amount_deleted))


    def __headers(self):
        self.base_headers = {
                "authority": "discordapp.com",                    #  0
                "x-super-properties": None,                       #  1
                "origin": None,                                   #  2
                "authorization": self.token,                      #  3
                "accept-language": self.language,                 #  4
                "user-agent": self.user_agent,                    #  5
                "content-type": None,                             #  6
                "accept": "*/*",                                  #  7
                "sec-fetch-site": "same-origin",                  #  8
                "sec-fetch-mode": "cors",                         #  9
                "referer": "https://discordapp.com/channels/@me", # 10
                "accept-encoding": "gzip, deflate, br",           # 11
                "cookie": self.cookies                            # 12
        }
        
        self.patch_headers = deepcopy(self.base_headers)
        self.patch_headers["x-super-properties"] = self.super_properties
        self.patch_headers["origin"] = "https://discordapp.com"
        self.patch_headers["content-type"] = "application/json"

        self.delete_headers = deepcopy(self.patch_headers)
        self.delete_headers.pop("content-type")

        self.get_headers = {k: v for k, v in deepcopy(self.base_headers).items()
                            if v is not None}
        self.patch_headers = {k: v for k, v in self.patch_headers.items()
                              if v is not None}
        self.delete_headers = {k: v for k, v in self.delete_headers.items()
                               if v is not None}


    def __retrieve(self):
        self.session.headers = self.get_headers
        params = {"before": self.last_ident, "limit": 50}
        req = self.session.get(self.base_url, params=params)

        if req.status_code != 200:
            raise ConnectionError("Could not retrieve any message")

        return req.content


    def __parse(self, messages):
        unserialized = loads(messages)
        
        if not unserialized: # No more messages
            return None

        self.last_ident = unserialized[-1]["id"]
        if self.is_numeric_user:
            return [(m["id"], m["content"]) for m in unserialized
                    if m["author"]["id"] == self.user]
        else:
            return [(m["id"], m["content"]) for m in unserialized
                    if "{}#{}".format(m["author"]["username"],
                                      m["author"]["discriminator"]) == self.user]


    def __overwrite(self, ident):
        payload = dumps({"content": "".join((choice(self.characters)
                                             for _ in range(randint(5, 250))))})
        self.session.headers = self.patch_headers
        req = self.session.patch("{}/{}".format(self.base_url, ident),
                                                data=payload)
        if req.status_code != 200:
            raise ConnectionError("An error occurred while overwriting a message")


    def __delete(self, ident):
        self.session.headers = self.delete_headers
        req = self.session.delete("{}/{}".format(self.base_url, ident))

        if req.status_code not in (200, 204):
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
                        help="ID of the Discord channel you want your " \
                             "messages deleted from")
    parser.add_argument("-r", "--restore", type=int,
                        help="ID of the last message seen (checkpoint)")
    parser.add_argument("-m", "--max-delete", default=maxsize, type=int,
                        help="maximum amount of messages to delete")
    parser.add_argument("--super-properties",
                        help="informations about your system")
    parser.add_argument("--language", default="en_GB",
                        help="language used by Discord")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT,
                        help="Discord user agent")
    parser.add_argument("--cookies", help="cookies (__cfduid, __cfruid, locale)")

    args = parser.parse_args()
    dys = Dyscordia(**vars(args))
    dys.shred()
