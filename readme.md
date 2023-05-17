# 🎙️ GPT Reviews

## An end-to-end* AI-generated podcast

Listen:

<img src="https://lh3.googleusercontent.com/uCn9RLCitLIaHYkIxzY-PvuErfWlEpTVU7xko6FOhbOi0ykPwNkInX2B2CwRmNNMgB5EHK-4Bs9DQUmnohdSdJan3fU7WofGGo1g3dqAIFg" alt="Spotify" class="xbGufb" style="width: 32px; height: 32px;" width="32" height="32"> 
<img src="https://lh5.googleusercontent.com/Mb4Ai2ZsCUQPqFIc4z2rM1CgEDMR9v4Yc0eFydV6jpoXrWIgkBHcW4b8_Xte_cU1fcA2VNE2JY7nk43KUuNlIjct91mTUEkBmlkIlT8n3FM" alt="Link" class="xbGufb" style="width: 32px; height: 32px;" width="32" height="32">
<img src="https://lh6.googleusercontent.com/IHtbTx7u577WFP5LEDkKmfFoiWKQo7jpFelBhr-ZnmjML0Kc5hmLg3fWTPXhHuEH1_uKQz4QSgm-8itmB3N8siwbYHDyTai393jZNzfIU78" alt="Link" class="xbGufb" style="width: 32px; height: 32px;" width="32" height="32">
<img src="https://lh6.googleusercontent.com/aT--jCTr4izx_WrYSHLOOSz1M8BrFJ2sgP2nFozJvFryGbADduCIE-ogHbd-Yj0ZyLmss-tlNsJEomeD5Tt3LP6DM6R6uWwkhdi3csLenhc" alt="Link" class="xbGufb" style="width: 32px; height: 32px;" width="32" height="32">
<img src="https://lh6.googleusercontent.com/aUv1TNrJUS1TnOz7V9_TZGPRKdlE6f5s_jTjttQBAssQQ1-N3XVoCBcD6M_dgs1EwGX303Sa_9veNeMEs8BBTIuCkBgqCOsTOmVpxK83iys" alt="Link" class="xbGufb" style="width: 32px; height: 32px;" width="32" height="32">

_*well there's no such thing as end to end is there. You feed it the news/papers/blogs you want and can also do manual editing of the scripts easily._

This is the code I use to generate the GPT Reviews podcast on a daily basis (Mon-Fri).

# How to run it yourselef
- You need an internet connection, LLMs and Text-to-speech doesn't run locally. 
- Getting audio assets into `assets/audio` from this public drive folder. They are .wav files to minimize encoding-decoding in read-write. The downside is they're pretty big, so I'm not committing them to the repo.
- Keys for openai and azure cognitive services should either be hardcocded (at your own risk) or set them as env variables as `OPENAIKEY` and `AZURE_SPEECH_KEY` respectively.
Yes the casing and underscoring is not consistent idk i probably set them up on different days and didn't bother changing them to something consistent later on.
- Hey sometimes the output parsing might fail a bit, which is why it's handy to save the scripts in .txt. You can look at them and fix things if you want.
It's often useful to reduce small wrong anoyances, such as Gio saying "our final news story" when it's story 2/3. ChatGPT is not that great at following many instructions so it's hard to make it do what i want it to do.
I'm quite confident GPT-4 fixes a lot of these things (I've played a bit with it but don't have access to it in my Earkind account yet...). So i totally plan on making the switch, perhaps for debugging it'll be expensive, but for daily episodes, hell yes.

# `content.txt` structure!!!
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

# More excuses on why the code is shitty
It runs on my laptop.

Okay so I tried to keep the code free from unnecessary abstractions, at the cost of some duplications and a long script that at least should be quite readable from the get-go.
There are no classes, only functions in blocks which do things that are self explanatory.

I thought about finding better ways to organize the code, but I think it only makes sense to do that organically once the project grows in complexity.
No LangChain and no nothing. I just use plain strings for prompt and I create a way to interpolate them with variables just marked as $VARIABLE. For now that's enough as well.

I avoid at all cost doing refinement calls to chatGPT (or whatever api). Responses should be a one-off + rule-based parsing. It might improve quality at some points but it's just much harder to debug and predict how consistent the LLM responses will be and so on... Besides, everything I could do with an interaction + refinement in chatGPT I can probably do in a single call to GPT-4, so I plan on migrating to that once I 

Probably the most low-hanging fruit in terms of making the code more clean is creating abstractions for the audio editing: like wrapping the stuff i do repeatedly like normalization, adding background music with certain fades and so on.
Still, it's a pain in the ass cause i want to have very fine-grained access to each audio file for settings like volume, so wrapping all the audio files in a dictionary or class for instance didn't make sense.
So i load all those files as separate variables with semantically relevant names.
There's probably a better way to do it, but it's okay for now.