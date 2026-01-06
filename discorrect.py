#!/usr/bin/env python3


"""
    [Discorrect - Message shredder for Discord - by Roen, 2020-2026]
"""


from argparse import ArgumentParser
from atexit import register
from copy import copy
from json import dumps, loads
from random import choice, randint, uniform
from requests import Session
from string import ascii_letters, digits, punctuation, whitespace
from sys import maxsize
from time import sleep


DEFAULT_USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.119 "
                      "Chrome/138.0.7204.251 Electron/37.6.0 Safari/537.36")


class Discorrect:

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

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
            "accept": "*/*",                                        #  0
            "accept-language": self.language,                       #  1
            "authorization": self.token,                            #  2
            #"accept-encoding": None,                               #  3
            "content-type": None,                                   #  4
            "cookie": self.cookies,                                 #  5
            "priority": "u=1, i",                                   #  6
            "referer": "https://discord.com/channels/@me",          #  7
            "origin": None,                                         #  8
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138"', #  9
            "sec-ch-ua-mobile": "?0",                               # 10
            "sec-ch-ua-platform": '"Linux"',                        # 11
            "sec-fetch-dest": "empty",                              # 12
            "sec-fetch-mode": "cors",                               # 13
            "sec-fetch-site": "same-origin",                        # 14
            "user-agent": self.user_agent,                          # 15
            "x-debug-options": "bugReporterEnabled",                # 16
            "x-discord-locale": self.locale,                        # 17
            "x-discord-timezone": self.timezone,                    # 18
            "x-super-properties": self.super_properties,            # 19
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

        return req.content


    def __parse(self, messages):
        unserialized = loads(messages)

        if not unserialized: # No more messages
            return None

        self.last_ident = unserialized[-1]["id"]

        id_or_name = "id" if self.user.isnumeric() else "username"
        return [(m["id"], m["content"], bool(m["attachments"]))
                for m in unserialized if m["author"][id_or_name] == self.user]


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
                        help="username or user ID")
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
    parser.add_argument("--language", default="en-GB,en;q=0.9,en;q=0.8",
                        help="language used by Discord")
    parser.add_argument("--locale", default="en-GB",
                        help="locale used by Discord")
    parser.add_argument("--timezone", default="Europe/London",
                        help="timezone used by Discord")
    parser.add_argument("--user-agent", default=DEFAULT_USER_AGENT,
                        help="Discord user agent")
    parser.add_argument("--cookies",
                        help="cookies (__dcfduid, __sdcfduid, etc.)")
    parser.add_argument("--super-properties",
                        help="informations about your system")

    args = parser.parse_args()
    dis = Discorrect(**vars(args))
    dis.shred()
