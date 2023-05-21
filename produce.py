import argparse
import os
import random
from datetime import datetime
import markdown
import randfacts
import logging
import pyjokes

from src.utils import load_content
from src.writing import write
from src.recording import speak, speak_conversation
from src.audio import AudioSegment

parser = argparse.ArgumentParser(description="Main Script for GPT Reviews")
parser.add_argument("scope", choices=["content", "scripts", "recordings", "all"],
                    help="Choose between 'content', 'scripts', 'recordings', 'all'")
parser.add_argument('--date', type=str, default="",
                    help="Specify the date of the pod episode as `yyyy-mm-dd`.\
                        Otherwise it'll take today as the time of running")
parser.add_argument('--log', type=str, default="INFO", dest="loglevel",
                    help="Speciify the log level from info, warning, debug, error")
args = parser.parse_args()

logging.basicConfig(handlers=[logging.FileHandler(f"{str(datetime.now())[:-7]}.log"), logging.StreamHandler()],
                    encoding="utf-8",
                    format="%(levelname)s:%(name)s: %(asctime)s %(message)s",
                    datefmt="%I:%M:%S %p",
                    level=getattr(logging, args.loglevel.upper()))

################################################################
########################## PREPROCESS! #########################

if not os.path.exists("assets-today/"):
    os.mkdir("assets-today/")
if not os.path.exists("assets-today/audio-clips/"):
    os.mkdir("assets-today/audio-clips/")
if not os.path.exists("assets-today/scripts/"):
    os.mkdir("assets-today/scripts/")
if not os.path.exists("assets-today/pdfs/"):
    os.mkdir("assets-today/pdfs/")
if not os.path.exists("episode/"):
    os.mkdir("episode/")

# FYI content is a list of dicts, and each item in the dict has keys
# {type, title, [...]}
content = load_content()

news = [item for item in content if item['type'] == 'news']
reads = [item for item in content if item['type'] == 'other']
papers = [item for item in content if item['type'] == 'paper']

char_limit = 6000

# loading prompts from files to dict
prompts = {}
base_dir = "assets/prompts/"
for fname in os.listdir(base_dir):
    # skip file extension, use underscore, more convenient for selecting
    # you might ask why not save the files with underscores?
    # Idk i hate how it looks
    key = fname.split(".")[0].replace("-", "_")
    with open(base_dir + fname) as f:
        prompts[key] = f.read()

# We want the date in natural language!
if not args.date:
    today = datetime.today().strftime("%A, %B %d, %Y")
else:
    today = datetime.strptime(args.date, "%Y-%m-%d")\
                    .strftime("%A, %B %d, %Y")
logging.info(f"Usind date: {today}")


################################################################
###################### WRITING SCRIPTS! ########################

if args.scope in ["scripts", "recordings", "all"]:
    # in chronological order, comments make it easier to skim
    # INTRO
    topics = "\n".join(item["title"] for item in content)
    intro_script = write(system_prompt=prompts['system_prompt_gio'],
                      user_prompt_template=prompts['user_prompt_intro'],
                      substitutions={"$DATE": today,
                                     "$FACT": randfacts.get_fact(),
                                     "$JOKE": pyjokes.get_joke(),
                                     "$TOPICS": topics},
                      script_path="assets-today/scripts/intro.txt",
                      temperature=1,
                      parsing_options={})
    
    # NEWS
    news_scripts = []
    for i, newspiece in enumerate(news):
        news_scripts.append(
            write(system_prompt=prompts['system_prompt_news_conversation'],
                  user_prompt_template=prompts['user_prompt_news_conversation'],
                  substitutions={"$TITLE": newspiece["title"],
                                 "$SOURCE": newspiece["source"],
                                 "$CONTENT": newspiece["content"][:char_limit],
                                 "$PROGRESS": f"{i+1}/{len(news)}"},
                  script_path=f"assets-today/scripts/news-{i+1}.txt",
                  temperature=0.7,
                  parsing_options={"delimiter": "[SCRIPT]", "delete_gio": True}
                  )
        )

    # TRANSITION 1
    topics = "; ".join([r['title'] for r in reads])
    transition_1 = write(system_prompt=prompts['system_prompt_reads'],
                         user_prompt_template=prompts['user_prompt_reads_transition'],
                         substitutions={"$TOPICS": topics},
                         script_path="assets-today/scripts/transition-1.txt",
                         temperature=1,
                         parsing_options={"delete_gio": True})
    
    # RANDOM READS
    reads_scripts = []
    for i, piece in enumerate(reads):
        reads_scripts.append(
            write(system_prompt=prompts['system_prompt_reads'],
                  user_prompt_template=prompts['user_prompt_reads_conversation'],
                  substitutions={"$TITLE": piece["title"],
                                 "$SOURCE": piece["source"],
                                 "$CONTENT": piece["content"][:char_limit],
                                 "$PROGRESS": f"{i+1}/{len(reads)}"},
                  script_path=f"assets-today/scripts/reads-{i+1}.txt",
                  temperature=0.7,
                  parsing_options={
                "delimiter": "[SCRIPT]", "delete_gio": True, "delete_parenthesis": True}
            )
        )

    # FAKE SPONSOR
    moods = ["Excitement", "Nostalgia", "Humor", "Fear", "Inspiration",
             "Relaxation", "Urgency", "Empathy", "Surprise", "Joyful"]
    mood = random.choice(moods)
    parsing_options = {
        "delimiter": "[SCRIPT]",
        "delete_gio": False,
        "delete_parenthesis": True
    }
    logging.info(f"Mood choice: {mood}")
    ad_script = write(system_prompt="",
                      user_prompt_template=prompts['user_prompt_ad_conversation'],
                      substitutions={"$MOOD": mood},
                      script_path="assets-today/scripts/ad.txt",
                      temperature=1,
                      parsing_options=parsing_options)

    # TRANSITION 2
    titles = "; ".join([p['title'] for p in papers])
    transition_2 = write(system_prompt=prompts['system_prompt_gio'],
                         user_prompt_template=prompts['user_prompt_transition'],
                         substitutions={"$PAPERTITLES": titles, "$AD": ad_script},
                         script_path="assets-today/scripts/transition-2.txt",
                         temperature=1,
                         parsing_options={})

    # PAPERS
    paper_scripts = []
    for i, paper, in enumerate(papers):
        paper_scripts.append(
            write(system_prompt=prompts['system_prompt_paper_conversation'],
                  user_prompt_template=prompts['user_prompt_paper_conversation'],
                  substitutions={"$TITLE": paper['title'],
                                 "$AUTHORS": paper['authors'],
                                 "$ORGS": paper['orgs'],
                                 "$ABSTRACT": paper['abstract'],
                                 "$EXTRA": paper['extra_content'],
                                 "$PROGRESS": f"{i+1}/{len(papers)}"},
                  script_path=f"assets-today/scripts/paper-{i+1}.txt",
                  temperature=0.7,
                  parsing_options={"delimiter": "[SCRIPT]", "delete_gio": True})
        )

    # OUTRO
    outro_script = write(system_prompt=prompts['system_prompt_gio'],
                      user_prompt_template=prompts['user_prompt_outro'],
                      substitutions={"$DATE": today,
                                     "$JOKE": pyjokes.get_joke()},
                      script_path="assets-today/scripts/outro.txt",
                      temperature=1,
                      parsing_options={})

################################################################
######################### RECORDING! ###########################

if args.scope in ["recordings", "all"]:
    intro_section = speak(script=intro_script,
                          audio_path="assets-today/audio-clips/intro.wav",
                          speaker={"name": "en-US-DavisNeural",
                                   "style": "angry"},
                          paragraph_silence=600,
                          sentence_silence=400)

    outro_section = speak(script=outro_script,
                          audio_path="assets-today/audio-clips/outro.wav",
                          speaker={"name": "en-US-DavisNeural",
                                   "style": "angry"},
                          paragraph_silence=600,
                          sentence_silence=400)

    transition_1_section = speak_conversation(
        script=transition_1,
        audio_path=f"assets-today/audio-clips/transition-1.wav",
        host={"name": "en-US-DavisNeural",
              "style": "angry"},
        guest={"name": "en-US-SaraNeural",
               "style": "unfriendly"},
        delimiter={"host": "G: ", "guest": "O: "},
        paragraph_silence=200,
        sentence_silence=400
    )

    transition_2_section = speak(script=transition_2,
                               audio_path="assets-today/audio-clips/transition-2.wav",
                               speaker={"name": "en-US-DavisNeural",
                                        "style": "angry"},
                               paragraph_silence=600,
                               sentence_silence=400)

    ad_section = speak_conversation(script=ad_script,
                                    audio_path="assets-today/audio-clips/ad.wav",
                                    host={"name": "en-US-NancyNeural",
                                          "style": "excited"},
                                    guest={"name": "en-US-TonyNeural",
                                           "style": "cheerful"},
                                    delimiter={"host": "J: ", "guest": "L: "},
                                    paragraph_silence=400,
                                    sentence_silence=400)

    news_sections = []
    for i, script in enumerate(news_scripts):
        news_sections.append(
            speak_conversation(script=script,
                               audio_path=f"assets-today/audio-clips/news-{i+1}.wav",
                               host={"name": "en-US-DavisNeural",
                                     "style": "angry"},
                               guest={"name": "en-US-JasonNeural",
                                      "style": "angry"},
                               delimiter={"host": "G: ", "guest": "R: "},
                               paragraph_silence=100,
                               sentence_silence=200)
        )

    reads_sections = []
    for i, script in enumerate(reads_scripts):
        reads_sections.append(
            speak_conversation(script=script,
                               audio_path=f"assets-today/audio-clips/reads-{i+1}.wav",
                               host={"name": "en-US-DavisNeural",
                                     "style": "angry"},
                               guest={"name": "en-US-SaraNeural",
                                      "style": "unfriendly"},
                               delimiter={"host": "G: ", "guest": "O: "},
                               paragraph_silence=200,
                               sentence_silence=400)
        )

    paper_sections = []
    for i, script in enumerate(paper_scripts):
        paper_sections.append(
            speak_conversation(script=script,
                               audio_path=f"assets-today/audio-clips/papers-{i+1}.wav",
                               host={"name": "en-US-DavisNeural",
                                     "style": "chat"},
                               guest={"name": "en-US-AriaNeural",
                                      "style": "chat"},
                               delimiter={"host": "G: ", "guest": "B: "},
                               paragraph_silence=200,
                               sentence_silence=400)
        )

################################################################
################## EDITING + DESCRIPTION!! #####################

if args.scope == "all":

    from src.audio import (
        loudness_targets,
        intro_theme, intro_bg,
        news_theme_first, news_theme_rest, news_theme_out,
        reads_theme, reads_theme_out,
        paper_switch, paper_ambiences,
        fake_sponsor_jingle, fake_sponsor_jingle_out, ad_music,
        outro_theme, outro_bg, outro_bg_drums, outro_bass
    )

    # To include in the automated pod description
    all_scripts = "\n".join([intro_script,
                             *news_scripts,
                             transition_1,
                             *reads_scripts, 
                             ad_script,
                             transition_2,
                             *paper_scripts,
                             outro_script])
    highlights = write(system_prompt="",
                       user_prompt_template=prompts['user_prompt_pod_highlights'],
                       substitutions={"$SCRIPT": all_scripts},
                       script_path="assets-today/scripts/highlights.txt",
                       temperature=0,
                       parsing_options={"delimiter": "[HIGHLIGHTS]"})
    pod_description = f"{highlights}\n\nContact: \
        [sergi@earkind.com](mailto:sergi@earkind.com)\n\nTimestamps:"

    program = AudioSegment.empty()

    #### INTRO ####
    intro_section = intro_section.overlay(intro_bg, loop=True)
    program = program.append(intro_theme, crossfade=0)

    pod_description += f"\n\n{program.get_timestamp()} Introduction"
    program = program.append(intro_section, crossfade=10)

    #### NEWS ####
    for i, news_section in enumerate(news_sections):
        if i == 0:
            news_section = news_section.pad(left=6000)
            background = news_theme_first.fade(
                to_gain=-11, start=5500, duration=1000)
        else:
            news_section = news_section.pad(left=3500)
            background = news_theme_rest.fade(
                to_gain=-11, start=3000, duration=1000)
        news_section = news_section.overlay(background, loop=True)
        pod_description += f"\n\n{program.get_timestamp()} [{news[i]['title']}]({news[i]['url']})"
        program = program.append(news_section, crossfade=50)
    program = program.append(news_theme_out, crossfade=50)

    #### READS ####
    if reads_scripts:
        program = program.append(transition_1_section)
        for i, read_section in enumerate(reads_sections):
            section = read_section.pad(left=4000, right=500)
            background = reads_theme.fade(
                to_gain=-21, start=4500, duration=1000)
            section = section.overlay(
                background, loop=True).fade_out(duration=100)
            pod_description += f"\n\n{program.get_timestamp()} [{reads[i]['title']}]({reads[i]['url']})"
            program = program.append(section, crossfade=1000)
    program = program.append(reads_theme_out, crossfade=1000)

    #### ADS ####
    pod_description += f"\n\n{program.get_timestamp()} Fake sponsor"
    ad_section = ad_section.pad(left=3000, right=5000)
    ad_section = ad_section.overlay(ad_music, loop=True)\
                           .fade_out(duration=4000)

    sponsor_section = fake_sponsor_jingle.append(ad_section, crossfade=1000)\
                                         .append(fake_sponsor_jingle_out, crossfade=200)

    program = program.append(sponsor_section)

    #### TRANSITION ####
    transition_2_section = transition_2_section.pad(left=1000)
    program = program.append(transition_2_section, crossfade=1000)

    #### PAPERS ####
    program = program.append(paper_switch, crossfade=700)
    for i, paper_section in enumerate(paper_sections):
        ambience = random.choice(paper_ambiences)
        paper_section = paper_section.overlay(ambience, loop=True)

        pod_description += f"\n\n{program.get_timestamp()} [{papers[i]['title']}]({papers[i]['url']})"
        program = program.append(paper_section, crossfade=20)
        program = program.append(paper_switch, crossfade=700)

    #### OUTRO ####
    # outro jingle is the same as the intro but with different drumfill
    program = program.append(outro_theme, crossfade=10)

    pod_description += f"\n\n{program.get_timestamp()} Outro"

    # then add the background chill that transitions to drums
    repetitions = int(len(outro_section) / len(outro_bg))
    outro_bg = outro_bg.append(
        outro_bg_drums * repetitions, crossfade=10)

    outro = outro_bg.overlay(outro_section)

    program = program.append(outro, crossfade=10)
    program = program.append(outro_bass, crossfade=10)

    proposed_title = write(
        system_prompt="",
        user_prompt_template=prompts["user_prompt_pod_titles"],
        substitutions={"$DESCRIPTION": pod_description},
        script_path="assets-today/scripts/proposed-title.txt",
        temperature=1,
        parsing_options={}
    )

    #### SAVING FINAL FILES ####
    now = str(datetime.now())[:-7]
    # POD DESCRIPTION!
    with open("episode/description.html", "w") as f:
        # this converts the markdown into html
        f.write(markdown.markdown(pod_description))
    with open("episode/proposed-title.txt", "w") as f:
        f.write(proposed_title)

    # AUDIO FILE!
    program_audio_file = f"episode/prorgam-{now}.m4a"
    logging.info(f"Exporting the whole episode into {program_audio_file}")
    program.export(program_audio_file, format="mp4", bitrate="256k")
