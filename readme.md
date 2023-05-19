<h1 align="center">🎙️ GPT Reviews</h1>
<p align="center">
Listen on:
</p>
<p align="center">
  <a href="https://open.spotify.com/show/2xvBhAct7kGYd6h9b8txhq?si=a36ba38be6074150"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/666172aa-9f2d-4c72-81c5-9efb45c7b73c" alt="Spotify" height="40"></a> 
  <a href="https://music.amazon.co.uk/podcasts/b32e4420-6d57-44ed-915d-e68316217df6/gpt-reviews"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/560e8295-07e0-4bb0-9457-530f066c82d3" alt="Amazon" height="40"></a>
  <a href="https://podcasts.apple.com/es/podcast/gpt-reviews/id1687287441"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/f1cfcf78-059b-4e02-8e04-2898d12a1ecb" alt="Apple" height="40"></a>
  <a href="https://podcasts.google.com/feed/aHR0cHM6Ly9hbmNob3IuZm0vcy9lMDgwOWM0OC9wb2RjYXN0L3Jzcw"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/66a010f8-15d1-4812-bdc4-f111face6fbc" alt="Google" height="40"></a>
  <a href="https://pca.st/hxzcjo0l"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/97c54422-4ef9-4485-9a86-2c406df19e7c" alt="Pocketcasts" class="xbGufb" height="40"></a>
  <a href="https://twitter.com/earkindtech"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/7dfc1c17-0073-4727-8f1d-a4a0da6a5142" alt="Twitter" height="40"></a>
</p>

This is the code I use to generate the GPT Reviews podcast on a daily basis (Mon-Fri).
Based on a bunch of raw news, papers, and random content it generates a podacst episode explaining and commenting on it.
Learn more about the project on the Earkind website, or on this blog post about my thinking behind it.
This is an ongoing personal project, code changes can be quick and messy! If you like this or have concrete ideas on how to imrpve it please reach out via [sergi@earkind.com](mailto:sergi@earkind.com) 🫶.

# How to run it yourselef

- First you need to get keys for OpenAI and Azure's Speech Service. Then set them as env variables as `OPENAIKEY` and `AZURE_SPEECH_KEY` respectively (or hardcode them at your own risk). You can find guides to obtain those keys HERE and HERE!!!! (ADDDDDD).
- Install ffmpeg via `brew install ffmpeg`. Then pray for the best. This package is required for the encode-decode of various audio formats, and when you google how to install it, you get 87 different options, most of which don't work for reasons I'm not even close to understanding. `brew` is the only one that worked for me on macOS. Otherwise, you'll have to investigate yourself.
- Install requirements via `pip install -r requirements.txt`
- Download the audio assets into `assets/audio` [here](https://drive.google.com/drive/folders/1XJpVxs0uN9zCgUnUov5mmCf6ooLyZBmM?usp=share_link). They are .wav files to minimize encoding-decoding in read-write. The downside is they're pretty big, so I'm not committing them to the repo.
Yes the casing and underscoring is not consistent idk i probably set them up on different days and didn't bother changing them to something consistent later on.
- Now it's time to define what you want your show to be about. Then add the content you want your episode to contain in `content.txt`. Follow the guidelines strictly explained below!
- `produce.py` is the main script and entrypoint. To produce the whole show you run `python produce.py {scope}` where `scope` can be `content` (only parse the content.txt into a content.json) `scripts` (generate program scripts), `recording` (generate voices) or `all` (include the editing + export to master audio file). You can also add a `--date` argument to specify the date to be used in the show in the format `YYYY-MM-DD`, and the logger level via `--log`.
- The files in `assets-today/` represent the _cache_ of the program. If a something needs to be generated, it'll always try to load it from there. Actually now that i write it, i can probably clean up the code using the cache abstraction.
- End-to-end generation is mostly okay, but sometimes scriptscan have undesirable stuff (e.g. a conversation script doesn't have the right speaker-markers and so on). The way you edit things manually is going under `assets-today/scripts/` and edit those text files. All the generated text and audios are cached as files, when running produce, if there's a cache for a script or audio, it'll be loaded from there. If you want to redo a whole section you need to delete that section's file first. For instance, if you want to change the script for a section and it was already generated with an audio file, delete the audio file, rewrite the script and run `python produce.py all` again.
- I use some manual editing to delete these annoyances such as as Gio saying "our final news story" when it's story 2/3. ChatGPT is not that great at following many instructions so it's hard to make it do what i want it to do. I'll try new prompting strategies to mitigate this but for now it's fairly fine. I'm quite confident GPT-4 fixes a lot of these things (I've played a bit with it but don't have access to it in my Earkind account yet...). So i totally plan on making the switch, perhaps for developing it's expensive, but for daily episodes, hell yes.
- `upload.py` is just something I use to upload the shows on an azure blob, you probably don't need it.


# `content.txt` structure
The principle of how you feed data into the whole thing is the following.
`content.txt` is meant to be a simple txt file to manipulate by you, the human generating the podcast.
Then this is parsed into `content.json` so it's easier to reuse and so on.
Initially i wanted to hook it up to a Notion DB or whatever i use to keep track of content but... i feel it introduces more complexity than it saves.
At the end of the day for now I choose to have editorial
It's importat to follow the structure in the `content.txt` file so things are parsed accordingly
- the file contains a list of the raw content to be used in the episode
- each item is separated by `---`
- the first line of each item indicates what type of content that is: `[NEWS]`, `[OTHER]` or `[PAPER]`. Yeah i hate that news is a weird name that cannot exist in singular form but whatever this is what it is for now.
- For papers, the next line is the arxiv url, for news and other types it's title, source/authors, url, content (multiline).
- For news and other content, the content part of the item will be capped at 6000 characters to avoid going over the context max. This is quite conservative, but the 1-shot prompt contains a lot of tokens and i don't want to risk it.
- Extra newlines are thrown away FYI.

# Code Structure

- `produce.py` is the 'canvas' where you define the recipe for the show. It's just a long script of all the stuff that happens. It should be slow but easy to follow.
- `assets/` where static assets live: audio files and prompts. Prompts are commited as code, audios are downloaded with the drive. Prompts can be seen as templates, as they contain variables, preceeded with the dollar-sign `$VARIABLE`. 
- `src/` the tools to define the program recipe. It's all functions, no classes, (except for the audio editing where there's a tinie tiny class extension).
I've tried to think of what abstractions made sense to express as classes, but it felt it added unnecessary complexity. My sense is once the prompt construction is a bit more complex and expressive (beyond simple substitutions), or once I want to hook different LM or TTS backends, then the abstractions will become clearer and will refactor on the go. `writing.py` contains text generation stuff, `recording.py` contains Text-to-speech stuff, `audio.py` contains audio stuff, and `utils.py` contains content loading/parsing/crawling stuff.

# Some thoughts on why things are the way they are

It runs on my laptop.

I avoid at all cost doing refinement calls to chatGPT (or whatever api). Responses should be a one-off + rule-based parsing. It might improve quality at some points but it's just much harder to debug and predict how consistent the LLM responses will be and so on... Besides, everything I could do with an interaction + refinement in chatGPT I can probably do in a single call to GPT-4, so I plan on migrating to that once I get access to it.

There's probably much better ways and I'll probably find them eventually.