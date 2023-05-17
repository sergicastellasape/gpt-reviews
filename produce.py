import argparse
import os
import random
from datetime import datetime
import markdown
import randfacts
import logging
import pyjokes
from pydub import AudioSegment

from src.utils import load_content
from src.writing import write
from src.recording import speak, speak_conversation
from src.editing import load_at_volume, adjust_volume, ms_to_time

parser = argparse.ArgumentParser(description="Main Script for GPT Reviews")
parser.add_argument("scope", choices=["content", "scripts", "recordings", "all"],
                    help="Choose between 'content', 'scripts', 'recordings', 'all'")
parser.add_argument('--date', type=str, default="",
                    help="Specify the date of the pod episode as `yyyy-mm-dd`.\
                        Otherwise it'll take today as the time of running")
parser.add_argument('--log', type=str, default="INFO", dest="loglevel",
                    help="Speciify the log level from info, warning, debug, error")
args = parser.parse_args()

logging.basicConfig(filename=f'{str(datetime.now())[:-7]}.log', encoding='utf-8',
                    format='%(levelname)s:%(name)s: %(asctime)s %(message)s', datefmt='%I:%M:%S %p',
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

################################################################
###################### WRITING SCRIPTS! ########################

news = [item for item in content if item['type'] == 'news']
reads = [item for item in content if item['type'] == 'other']
papers = [item for item in content if item['type'] == 'paper']

char_limit = 6000

# loading prompts from files to dict
prompts = {}
base_dir = "assets/prompts/"
for fname in os.listdir("assets/prompts/"):
    # skip file extension, use underscore, more convenient for selecting
    # you might ask why not save the files with underscores?
    # Idk i hate how it looks
    key = fname.split(".")[0].replace("-", "_")
    with open(base_dir + fname) as f:
        prompts[key] = f.read()

# get date in natural language
if not args.date:
    today = datetime.today().strftime("%A, %B %d, %Y")
else:
    today = datetime.strptime(args.date, "%Y-%m-%d")\
                    .strftime("%A, %B %d, %Y")
logging.info(f"Usind date: {today}")

if args.scope in ["scripts", "recordings", "all"]:
    # in chronological order, comments make it easier to skim
    # INTRO
    topics = "\n".join(item["title"] for item in content)
    gio_intro = write(system_prompt=prompts['system_prompt_gio'],
                      user_prompt_template=prompts['user_prompt_intro'],
                      substitutions={"$DATE": today,
                                     "$FACT": randfacts.get_fact(),
                                     "$JOKE": pyjokes.get_joke(),
                                     "$TOPICS": topics},
                      script_path="assets-today/scripts/gio-intro.txt",
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
    transition1 = write(system_prompt=prompts['system_prompt_reads'],
                        user_prompt_template=prompts['user_prompt_reads_transition'],
                        substitutions={"$TOPICS": topics},
                        script_path="assets-today/scripts/transition1.txt",
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
    transition2 = write(system_prompt=prompts['system_prompt_gio'],
                        user_prompt_template=prompts['user_prompt_transition'],
                        substitutions={"$PAPERTITLES": titles, "$AD": ad_script},
                        script_path="assets-today/scripts/transition2.txt",
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
    gio_outro = write(system_prompt=prompts['system_prompt_gio'],
                      user_prompt_template=prompts['user_prompt_outro'],
                      substitutions={"$DATE": today,
                                     "$JOKE": pyjokes.get_joke()},
                      script_path="assets-today/scripts/gio-outro.txt",
                      temperature=1,
                      parsing_options={})

################################################################
######################### RECORDING! ###########################

if args.scope in ["recordings", "all"]:
    intro_section = speak(script=gio_intro,
                          audio_path="assets-today/audio-clips/gio-intro.wav",
                          speaker={"name": "en-US-DavisNeural",
                                   "style": "angry"},
                          paragraph_silence=600,
                          sentence_silence=400)

    outro_section = speak(script=gio_outro,
                          audio_path="assets-today/audio-clips/gio-outro.wav",
                          speaker={"name": "en-US-DavisNeural",
                                   "style": "angry"},
                          paragraph_silence=600,
                          sentence_silence=400)

    transition1_section = speak_conversation(
        script=transition1,
        audio_path=f"assets-today/audio-clips/transition1.wav",
        host={"name": "en-US-DavisNeural",
              "style": "angry"},
        guest={"name": "en-US-SaraNeural",
               "style": "unfriendly"},
        delimiter={"host": "G: ", "guest": "O: "},
        paragraph_silence=200,
        sentence_silence=400
    )

    transition_section = speak(script=transition2,
                               audio_path="assets-today/audio-clips/transition2.wav",
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
##################### AUDIO HOUSEKEEPING! ######################

if args.scope == "all":
    # audio editing after all clips shave been created
    logging.info("WORKING ON THE AUDIO EDITING")
    background_loudness_target = -26
    ambient_loudness_target = -36
    narration_loudness_target = -21
    theme_target_loudness = -15

    # adjust all narration volumes
    intro_section = adjust_volume(intro_section, narration_loudness_target)
    outro_section = adjust_volume(outro_section, narration_loudness_target)
    ad_section = adjust_volume(ad_section, narration_loudness_target)
    transition1_section = adjust_volume(transition1_section, narration_loudness_target)
    transition_section = adjust_volume(transition_section,narration_loudness_target)
    news_sections = [adjust_volume(section, narration_loudness_target)
                     for section in news_sections]
    reads_sections = [adjust_volume(section, narration_loudness_target)
                      for section in reads_sections]
    paper_sections = [adjust_volume(section, narration_loudness_target)
                      for section in paper_sections]

    # load all audio assets
    logging.info("Loading audio assets")
    # INTRO
    jingle_intro = load_at_volume("assets/audio/intro.wav", theme_target_loudness)
    background_intro = load_at_volume("assets/audio/daily-intro-bg.wav", background_loudness_target)

    # NEWS
    jingle_news_and_background_1 = load_at_volume("assets/audio/news-start.wav", narration_loudness_target - 4)
    jingle_news_and_background_2 = load_at_volume("assets/audio/news-transition.wav", narration_loudness_target - 4)
    jingle_news_out = load_at_volume("assets/audio/news-out.wav", narration_loudness_target - 2)

    # READS
    background_reads = load_at_volume("assets/audio/reads-bg.wav", narration_loudness_target - 4)
    jingle_reads_jout = load_at_volume("assets/audio/reads-out.wav", narration_loudness_target - 4)

    # PAPERS
    jingle_paper_switch = load_at_volume("assets/audio/reversed-guitar.wav", narration_loudness_target)

    # FAKE SPONSOR
    fake_sponsor_jingle = load_at_volume("assets/audio/fake-sponsor-jingle.wav", narration_loudness_target)
    fake_sponsor_jingle_out = load_at_volume("assets/audio/fake-sponsor-jingle-out.wav", narration_loudness_target)
    ad_music = load_at_volume(f"assets/audio/ad-music.m4a", background_loudness_target)

    # OUTRO
    jingle_outro = load_at_volume("assets/audio/outro.wav", theme_target_loudness)
    background_outro = load_at_volume("assets/audio/daily-outro-no-drums.wav", background_loudness_target + 6)
    background_outro_with_drums = load_at_volume("assets/audio/daily-outro-drums.wav", background_loudness_target + 6)
    bass_finale = load_at_volume("assets/audio/bass-out.wav", background_loudness_target + 6)

    ################################################################
    ################## EDITING + DESCRIPTION!! #####################

    # To include in the automated pod description
    all_scripts = "\n".join([gio_intro,
                             *news_scripts,
                             transition1,
                             *reads_scripts, 
                             ad_script,
                             transition2,
                             *paper_scripts,
                             gio_outro])
    highlights = write("",
                       user_prompt_template=prompts['user_prompt_pod_highlights'],
                       substitutions={"$SCRIPT": all_scripts},
                       script_path="assets-today/scripts/highlights.txt",
                       temperature=0,
                       parsing_options={"delimiter": "[HIGHLIGHTS]"})
    pod_description = f"{highlights}\n\nContact: [sergi@earkind.com](mailto:sergi@earkind.com)\n\nTimestamps:"

    program = AudioSegment.empty()

    #### INTRO ####
    intro_section = intro_section.overlay(background_intro, loop=True)
    program = program.append(jingle_intro, crossfade=0)

    pod_description += f"\n\n{ms_to_time(len(program))} Introduction"
    program = program.append(intro_section, crossfade=10)

    #### NEWS ####
    for i, news_section in enumerate(news_sections):
        if i == 0:
            news_section = AudioSegment.silent(duration=6000)\
                                       .append(news_section, crossfade=5)
            background = jingle_news_and_background_1.fade(
                to_gain=-11, start=5500, duration=1000)
        else:
            news_section = AudioSegment.silent(
                duration=3500).append(news_section, crossfade=5)
            background = jingle_news_and_background_2.fade(
                to_gain=-11, start=3000, duration=1000)
        news_section = news_section.overlay(background, loop=True)
        pod_description += f"\n\n{ms_to_time(len(program))} [{news[i]['title']}]({news[i]['url']})"
        program = program.append(news_section, crossfade=50)
    program = program.append(jingle_news_out, crossfade=50)

    #### READS ####
    if reads_scripts:
        program = program.append(transition1_section)
        for i, read_section in enumerate(reads_sections):
            section = AudioSegment.silent(duration=4000)\
                .append(read_section, crossfade=5)\
                .append(AudioSegment.silent(duration=500), crossfade=0)
            background = background_reads.fade(
                to_gain=-21, start=4500, duration=1000)
            section = section.overlay(
                background, loop=True).fade_out(duration=100)
            pod_description += f"\n\n{ms_to_time(len(program))} [{reads[i]['title']}]({reads[i]['url']})"
            program = program.append(section, crossfade=1000)
    program = program.append(jingle_reads_jout, crossfade=1000)

    #### ADS ####
    pod_description += f"\n\n{ms_to_time(len(program))} Fake sponsor"
    ad_section = AudioSegment.silent(duration=3000)\
                             .append(ad_section)\
                             .append(AudioSegment.silent(duration=5000))
    ad_section = ad_section.overlay(ad_music, loop=True)\
                           .fade_out(duration=4000)

    sponsor_section = fake_sponsor_jingle.append(ad_section, crossfade=1000)\
                                         .append(fake_sponsor_jingle_out, crossfade=200)

    program = program.append(sponsor_section)

    #### TRANSITION ####
    transition_section = AudioSegment.silent(
        duration=1000).append(transition_section, crossfade=0)
    program = program.append(transition_section, crossfade=1000)

    #### PAPERS ####
    program = program.append(jingle_paper_switch, crossfade=700)
    for i, paper_section in enumerate(paper_sections):
        fname = f"assets/audio/ambient-{random.randrange(1,6)}.wav"
        background_ambience = load_at_volume(fname, ambient_loudness_target)

        paper_section = paper_section.overlay(background_ambience, loop=True)

        pod_description += f"\n\n{ms_to_time(len(program))} [{papers[i]['title']}]({papers[i]['url']})"
        program = program.append(paper_section, crossfade=20)
        program = program.append(jingle_paper_switch, crossfade=700)

    #### OUTRO ####
    # outro jingle is the same as the intro but with different drumfill
    program = program.append(jingle_outro, crossfade=10)

    pod_description += f"\n\n{ms_to_time(len(program))} Outro"

    # then add the background chill that transitions to drums
    repetitions = int(len(outro_section) / len(background_outro))
    background = background_outro.append(
        background_outro_with_drums * repetitions, crossfade=10)

    outro_section = outro_section.append(AudioSegment.silent(duration=7000))
    outro = background.overlay(outro_section)

    program = program.append(outro, crossfade=10)
    program = program.append(bass_finale, crossfade=10)

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
        f.write(markdown.markdown(pod_description)
                )
    with open("episode/proposed-title.txt", "w") as f:
        f.write(proposed_title)

    # AUDIO FILE!
    program_audio_file = f"episode/prorgam-{now}.m4a"
    logging.info(f"Exporting the whole episode into {program_audio_file}")
    program.export(program_audio_file, format="mp4", bitrate="256k")
