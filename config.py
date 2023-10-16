# we define the argparsing here such that we can use these stuff as global
# variables in the program which is more convenient than loading them in the
# main produce.py script. Mainly the usecase is to define OpenAI's model
# name here instead of passing it at every write() or generate() function call.
# This could be controversial but I think for now we'll always be generating
# everything with the same model (prompts are tuned for a specific snapshot of a model)
# so I think it's safe to treat it as a global variable for now.

import argparse

parser = argparse.ArgumentParser(description="Main Script for GPT Reviews")
parser.add_argument("scope", choices=["content", "scripts", "recordings", "all"],
                    help="Choose between 'content', 'scripts', 'recordings', 'all'")
parser.add_argument("--date", type=str, default="",
                    help="Specify the date of the pod episode as `yyyy-mm-dd`.\
                        Otherwise it'll take today as the time of running")
parser.add_argument("--log", type=str, default="INFO", dest="loglevel",
                    help="Speciify the log level from info, warning, debug, error")
# important to use the snapshot 0301 cause the prompts are not optimized for the newer models
# and shit gets worse. Especially newer models have a bias for longer output which is annoying.
# Prompts will need to be tweaked for newer versions as I expect older snapshots to be deprecated
parser.add_argument("--model", type=str, default="gpt-3.5-turbo-0613", dest="model",
                    help="String identifier for the model passed to the OpenAI API.")

ARGS = parser.parse_args()
# this is an approximation to truncate content so prompts don't go beyond a model's context window.
# it's more convenient to truncate according to characters instead of tokens (albeit less accurate)
CHAR_LIMIT = 30000 if "16k" in ARGS.model else 6000
