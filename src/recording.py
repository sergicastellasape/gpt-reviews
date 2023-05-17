import os
from pydub import AudioSegment
from xml.etree.ElementTree import Element, SubElement, tostring

import azure.cognitiveservices.speech as speechsdk

azure_speech_key = os.getenv('AZURE_SPEECH_KEY')
boilerplate_ssml = {
    "version": "1.0",
    "xmlns": "http://www.w3.org/2001/10/synthesis",
    "xmlns:mstts": "http://www.w3.org/2001/mstts",
    "xmlns:emo": "http://www.w3.org/2009/10/emotionml",
    "xml:lang": "en-US",
}

def speak(script,
          audio_path,
          speaker,
          paragraph_silence,
          sentence_silence):
    if not os.path.exists(audio_path):
        ssml = text2ssml(script,
                         speaker=speaker,
                         paragraph_silence=paragraph_silence,
                         sentence_silence=sentence_silence)
        print(f"Recording audio into {audio_path}")
        audio = ssml2audio(ssml)
        audio.export(audio_path, format="wav")
    else:
        print(f"Loading audio from {audio_path}")
        audio = AudioSegment.from_file(audio_path, format="wav")
    return audio


def speak_conversation(script,
                       audio_path,
                       host,
                       guest,
                       delimiter,
                       paragraph_silence,
                       sentence_silence):
    if not os.path.exists(audio_path):
        print(f"Recording conversation into {audio_path}")
        ssml = convo2ssml(script,
                          host=host,
                          guest=guest,
                          delimiter=delimiter,
                          paragraph_silence=paragraph_silence,
                          sentence_silence=sentence_silence)
        section = ssml2audio(ssml)
        section.export(audio_path, format="wav")
    else:
        print(f"Loading conversation from {audio_path}")
        section = AudioSegment.from_file(audio_path, format="wav")
        # sections.append(section)
    return section


def ssml2audio(ssml):
    speech_config = speechsdk.SpeechConfig(
        subscription=azure_speech_key, region="westeurope")
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff44100Hz16BitMonoPcm)
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None)
    result = synthesizer.speak_ssml_async(ssml).get()
    return AudioSegment(result.audio_data)


def text2ssml(text, speaker, paragraph_silence=200, sentence_silence=150):
    speaking_attr = boilerplate_ssml
    voice_attr = {"name": speaker['name'],
                  "tailingsilence-exact": f"{paragraph_silence}ms",
                  "sentenceboundarysilence-exact": f"{sentence_silence}ms"}
    voice_attr = {"name": speaker['name']}
    style_attr = {"style": speaker['style']}

    root = Element('speak', speaking_attr)
    voice_ = SubElement(root, "voice", voice_attr)
    style_ = SubElement(voice_, "mstts:express-as", style_attr)
    style_.text = text
    return tostring(root, encoding='unicode')


def convo2ssml(text,
               host={"name": "en-US-DavisNeural", "style": "angry"},
               guest={"name": "en-US-JasonNeural", "style": "angry"},
               delimiter={"host": "G: ", "guest": "R: "},
               paragraph_silence=100,
               sentence_silence=200):

    speakers = {"host": host, "guest": guest}
    convo = [turn for turn in text.split("\n") if turn]

    convo_tup = []

    for turn in convo:
        if turn[:3] == delimiter["host"]:
            convo_tup.append(("host", turn.split(delimiter["host"])[-1]))
        elif turn[0:3] == delimiter["guest"]:
            convo_tup.append(("guest", turn.split(delimiter["guest"])[-1]))
        else:
            print("Warning! skipping turn as no person was found")

    speaking_attr = boilerplate_ssml
    root = Element('speak', speaking_attr)
    for type_, text in convo_tup:
        voice_attr = {"name": speakers[type_]["name"],
                      "tailingsilence-exact": f"{paragraph_silence}ms",
                      "sentenceboundarysilence-exact": f"{sentence_silence}ms"}
        style_attr = {"style": speakers[type_]["style"]}
        voice_ = SubElement(root, "voice", voice_attr)
        style_ = SubElement(voice_, "mstts:express-as", style_attr)
        style_.text = text
    return tostring(root, encoding='unicode')
