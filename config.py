# we define the argparsing here such that we can use these stuff as global
# variables in the program which is more convenient. We can also use
# it to define other global variables

import argparse

parser = argparse.ArgumentParser(description="Main Script for GPT Reviews")
parser.add_argument("scope", choices=["content", "scripts", "recordings", "all"],
                    help="Choose between 'content', 'scripts', 'recordings', 'all'")
parser.add_argument("--date", type=str, default="",
                    help="Specify the date of the pod episode as `yyyy-mm-dd`.\
                        Otherwise it'll take today as the time of running")
parser.add_argument("--log", type=str, default="INFO", dest="loglevel",
                    help="Speciify the log level from info, warning, debug, error")
parser.add_argument("--model", type=str, default="gpt-3.5-turbo", dest="model",
                    choices=["gpt-3.5-turbo", "gpt-3.5-turbo-16k"],
                    help="String identifier for the model passed to the OpenAI API.")

ARGS = parser.parse_args()
CHAR_LIMIT = 6000 if ARGS.model == "gpt-3.5-turbo" else 30000