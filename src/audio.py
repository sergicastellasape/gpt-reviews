from pydub import AudioSegment
import logging


class AudioSegmentPlus(AudioSegment):
    """Extending AudioSegmentPlus with a few uesful methods.
    Following the same design pattern from AudioSegmentPlus,
    AudioSegmentPlus are *immutable* objects"""

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data=data, *args, **kwargs)

    def to_volume(self, volume):
        # subtracting two neg numbers always breaks the brain
        return self - (self.dBFS - volume)

    def pad(self, left=0, right=0):
        audio = (
            AudioSegmentPlus.silent(duration=left)
            .append(self, crossfade=0)
            .append(AudioSegmentPlus.silent(duration=right), crossfade=0)
        )
        return audio

    def get_timestamp(self):
        total_seconds = len(self) // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


# The reason volume normalization needs a lot of tweaks
# is that the RMS loudness measure we get from Pydub is
# averaged over a whole segment. Getting reads for something
# like the highest short-term loudness (e.g. ~3s) could
# give more consistent results...
loudness_targets = {
    "narration": -21,
    "theme": -15,
    "background": -26,
    "ambient": -36,
}

logging.info("Loading audio assets")
# INTRO
intro_theme = AudioSegmentPlus.from_file("assets/audio/intro.wav").to_volume(
    loudness_targets["theme"]
)
intro_bg = AudioSegmentPlus.from_file(
    "assets/audio/daily-intro-bg.wav"
).to_volume(loudness_targets["background"])

# NEWS
news_theme_first = AudioSegmentPlus.from_file(
    "assets/audio/news-start.wav"
).to_volume(loudness_targets["narration"] - 4)
news_theme_rest = AudioSegmentPlus.from_file(
    "assets/audio/news-transition.wav"
).to_volume(loudness_targets["narration"] - 4)
news_theme_out = AudioSegmentPlus.from_file(
    "assets/audio/news-out.wav"
).to_volume(loudness_targets["narration"] - 2)

# READS
reads_theme = AudioSegmentPlus.from_file(
    "assets/audio/reads-bg.wav"
).to_volume(loudness_targets["narration"] - 4)
reads_theme_out = AudioSegmentPlus.from_file(
    "assets/audio/reads-out.wav"
).to_volume(loudness_targets["narration"] - 4)

# PAPERS
paper_switch = AudioSegmentPlus.from_file(
    "assets/audio/reversed-guitar.wav"
).to_volume(loudness_targets["narration"])
paper_ambiences = [
    AudioSegmentPlus.from_file(f"assets/audio/ambient-{i}.wav").to_volume(
        loudness_targets["ambient"]
    )
    for i in range(1, 6)
]

# FAKE SPONSOR
fake_sponsor_jingle = AudioSegmentPlus.from_file(
    "assets/audio/fake-sponsor-jingle.wav"
).to_volume(loudness_targets["narration"])
fake_sponsor_jingle_out = AudioSegmentPlus.from_file(
    "assets/audio/fake-sponsor-jingle-out.wav"
).to_volume(loudness_targets["narration"])
ad_music = AudioSegmentPlus.from_file(f"assets/audio/ad-music.m4a").to_volume(
    loudness_targets["background"]
)

# OUTRO
outro_theme = AudioSegmentPlus.from_file("assets/audio/outro.wav").to_volume(
    loudness_targets["theme"]
)
outro_bg = AudioSegmentPlus.from_file(
    "assets/audio/daily-outro-no-drums.wav"
).to_volume(loudness_targets["background"] + 6)
outro_bg_drums = AudioSegmentPlus.from_file(
    "assets/audio/daily-outro-drums.wav"
).to_volume(loudness_targets["background"] + 6)
outro_bass = AudioSegmentPlus.from_file("assets/audio/bass-out.wav").to_volume(
    loudness_targets["background"] + 6
)
