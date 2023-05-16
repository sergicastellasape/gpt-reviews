from pydub import AudioSegment

def adjust_volume(audio, target):
    audio -= audio.dBFS - target
    return audio


def load_at_volume(fpath, target=-30):
    audio = AudioSegment.from_file(fpath)
    audio = adjust_volume(audio, target)
    return audio


def ms_to_time(ms):
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"
