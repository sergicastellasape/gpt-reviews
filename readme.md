<h1 align="center">🎙️ GPT Reviews</h1>
<p align="center">
Listen on:

<p align="center">
  <a href="https://open.spotify.com/show/2xvBhAct7kGYd6h9b8txhq?si=a36ba38be6074150"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/1/19/Spotify_logo_without_text.svg/1024px-Spotify_logo_without_text.svg.png" alt="Spotify" height="40"></a> 
  <a href="https://music.amazon.co.uk/podcasts/b32e4420-6d57-44ed-915d-e68316217df6/gpt-reviews"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/560e8295-07e0-4bb0-9457-530f066c82d3" alt="Amazon" height="40"></a>
  <a href="https://podcasts.apple.com/es/podcast/gpt-reviews/id1687287441"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/f1cfcf78-059b-4e02-8e04-2898d12a1ecb" alt="Apple" height="40"></a>
  <a href="https://podcasts.google.com/feed/aHR0cHM6Ly9hbmNob3IuZm0vcy9lMDgwOWM0OC9wb2RjYXN0L3Jzcw"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/66a010f8-15d1-4812-bdc4-f111face6fbc" alt="Google" height="40"></a>
  <a href="https://pca.st/hxzcjo0l"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/97c54422-4ef9-4485-9a86-2c406df19e7c" alt="Pocketcasts" class="xbGufb" height="40"></a>
  <a href="https://twitter.com/earkindtech"><img src="https://github.com/sergicastellasape/semantic-compression/assets/33417180/7dfc1c17-0073-4727-8f1d-a4a0da6a5142" alt="Twitter" height="40"></a>
</p>


This is the code I use to generate the GPT Reviews podcast on a daily basis (Mon-Fri).
Based on a bunch of raw news, papers, and random content it generates a podacst episode explaining and commenting on it.
Learn more about the project on the [Earkind website](https://www.earkind.com)

This is an ongoing personal project, code changes can be quick and messy! If you like this or have concrete ideas on how to imrpve it please reach out via [sergi@earkind.com](mailto:sergi@earkind.com) 🫶.

# Table of Contents

- [Generate your own episode](#✍️-generate-your-own-episode)
- [content.txt file structure](#𝌞-structure-of-contenttxt)
- [Code structure](#code-structure)
- [Thoughts](#some-thoughts-on-why-things-are-the-way-they-are)

# ✍️ Generate your own episode

- First, get keys for OpenAI and Azure's Speech Service. Then set them as env variables as `OPENAIKEY` and `AZURE_SPEECH_KEY` respectively (or hardcode them at your own risk). Here's a [howto for OpenAI keys](https://www.howtogeek.com/885918/how-to-get-an-openai-api-key/), and a howto for [Azure Speech Service keys](https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/get-started-speech-to-text).
- Install ffmpeg via `brew install ffmpeg`. Then pray for the best. This package is required for the encode-decode of various audio formats, and when you google how to install it, you get 87 different options, most of which don't work for reasons I'm not even close to understanding. `brew` is the only one that worked for me on macOS. Otherwise, you'll have to investigate yourself.
- Install requirements via `pip install -r requirements.txt`
- Download the audio assets into `assets/audio` [from my gdrive](https://drive.google.com/drive/folders/1XJpVxs0uN9zCgUnUov5mmCf6ooLyZBmM?usp=share_link). They are .wav files to minimize encoding-decoding in read-write. Warning: at some point I might change the names of the assets!
- Now it's time to define what you want your show to be about. This is done via the `content.txt` file. That's the human interface to define what the program will be about. Follow the guidelines from the [next section](#𝌞-structure-of-contenttxt).
- `produce.py` is the main script and entrypoint. To produce the whole show you run `python produce.py {scope}` where `scope` can be `content` (only parse the content.txt into a content.json) `scripts` (generate program scripts), `recording` (generate voices) or `all` (include the editing + export to master audio file). You can also add a `--date` argument to specify the date to be used in the show in the format `YYYY-MM-DD`, and the logger level via `--log`.
- The files created in `assets-today/` represent the _cache_ of the program. If a something needs to be generated, it'll always try to load it from there. Actually now that i write it, i can probably clean up the code using the cache abstraction.
- End-to-end generation is mostly okay, but sometimes scriptscan have undesirable stuff (e.g. a conversation script doesn't have the right speaker-markers and so on). The way you edit things manually is going under `assets-today/scripts/` and edit those text files. That's why a useful workflow is to only generate scripts, proofread them, then generate audios. All the generated text and audios are cached as files, when running produce, if there's a cache for a script or audio, it'll be loaded from there. If you want to redo a whole section you need to delete that section's file first. For instance, if you want to change the script for a section and it was already generated with an audio file, delete the audio file, rewrite the script and run `python produce.py all` again.
- I use some manual editing to delete these annoyances such as as Gio saying "our final news story" when it's story 2/3. ChatGPT is not that great at following many instructions so it's hard to make it do what i want it to do. I'll try new prompting strategies to mitigate this but for now it's fairly fine. I'm quite confident GPT-4 fixes a lot of these things (I've played a bit with it but don't have access to it in my Earkind account yet...). So i totally plan on making the switch, perhaps for developing it's expensive, but for daily episodes, hell yes.


# 𝌞 Structure of `content.txt`
The principle of how you feed data into the whole thing is the following.
`content.txt` is meant to be a simple txt file to manipulate by you, the human generating the podcast.
Then this is parsed into `content.json` so it's more convenient to mangle in the program.
Initially i wanted to hook it up to a Notion DB or whatever i use to keep track of content but... i feel it introduces more complexity than it saves.
At the end of the day I still want to choose the content in there.
It's importat to follow the structure in the `content.txt` file so things are parsed accordingly
- The file contains a list of the raw content to be used in the episode, and each item is separated by `---`.
- The first line of each item indicates what type of content that is: `[NEWS]`, `[OTHER]` or `[PAPER]`. Yeah i hate that news is a weird name that doesnt make sense in singular form but whatever this is what it is for now.
- For papers, the next line is the arxiv url (other stuff is scraped from arxiv).
- For news and other types it's title, source/authors, url, content (multiline). Scraping is less consistent so i just copypaste the interesting things.
- For news and other content, the content part of the item will be capped at `chat_limit` characters to prevent maxxing the context 4k context. This is quite conservative, but the 1-shot prompt contains a lot of tokens and i don't want to risk it.

- Empty lines are thrown away, FYI.

# Code Structure

- `produce.py` is the 'canvas' where show recipe is defined. It's just a long script of all the stuff that happens. It should be verbose but easy to follow.
- `assets/` where static assets live: audio files and prompts. Prompts are commited as code, audios are downloaded with the drive. Prompts can be seen as templates, as they contain variables, preceeded with the dollar-sign `$VARIABLE`. 
- `src/` the tools to define the program recipe. It's all functions, no classes, (except for the audio editing where there's a tinie tiny class extension).
I've tried to think of what abstractions made sense to express as classes, but it felt it added unnecessary complexity. My sense is once I start hooking up different LM or TTS backends, it'll make sense and the abstractions will become clearer.
  - `writing.py` contains text generation stuff
  - `recording.py` contains Text-to-speech stuff
  - `audio.py` contains audio stuff
  - `utils.py` contains content loading/parsing/crawling stuff
  - `upload.py` is just something I use to upload the shows on an azure blob, you probably don't need it.

# Some thoughts on why things are the way they are

I promise it runs on my laptop.

I avoid at all cost doing refinement calls to chatGPT. Responses should be a one-off + rule-based parsing. It might improve quality at some point, but just adds complexity that makes me feel gross when i feel the one-off route hasn't been maximized... Besides, everything I could do with an interaction + refinement in chatGPT I can probably do in a single call to GPT-4, so I plan on migrating to that once I get access to it. Also I want to first add anthropics LM backend and only implement it in a way that backends can be swapped easily.

Don't want to use LangChain, it confuses me still and it doesn't feel like i need it. Besides, figuring out the templating and chaining is fun and a valuable learning experience. But who knows, once the prompt building is more complex i might need to jump there.

I still like having the editorial control over what goes into the show. In the future you could also automate that and select content based on an automated recommendation system, even a personalized one where every user gets a different pod.
For now I don't want to go down that rabbithole but, for the next show I might prioritize that and choose content that is easyly selectable automatically (e.g. top hackernews recap [like this podcast](https://foundr.ai/product/hacker-news-recap))
