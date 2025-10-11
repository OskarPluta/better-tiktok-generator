import re
import torch
import os 
import shutil
import random

import torchaudio as ta

from chatterbox.tts import ChatterboxTTS
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
from moviepy import AudioFileClip, CompositeAudioClip
from moviepy import afx
from utils import chunk_text

class AudioMaker:

    TEMP_DIR = "./temp_audio"
    MUSIC_VOLUME = 0.005
    TTS_VOLUME = 1.0

    device = "cpu"


    def __init__(self):
        pass
    
    def create_tts(self, text: str, language: str, speaker_wav: str, output_dir: str,
                   exaggeration: float = 0.5, cfg_weight: float = 0.5, 
                   temperature: float = 0.8, repetition_penalty: float = 2, 
                   min_p : float = 0.05, top_p: float = 1):
        model = ChatterboxMultilingualTTS.from_pretrained(device=AudioMaker.device)
        temp_dir = AudioMaker.TEMP_DIR
        silence_duration = 0.1

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        chunks = chunk_text(text)

        file_paths = []

        print(f"The text was split into {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"Chunk: {i}")

            wav_chunk = model.generate(chunk, language_id=language, audio_prompt_path=speaker_wav, exaggeration=exaggeration, cfg_weight=cfg_weight, temperature=temperature, repetition_penalty=repetition_penalty, min_p=min_p, top_p=top_p)
            file_path = os.path.join(temp_dir, f"chunk_{i}.wav")
            ta.save(file_path, wav_chunk, model.sr)
            file_paths.append(file_path)

            del wav_chunk

        silence = torch.zeros(int(model.sr * silence_duration))
        all_audio = []

        for i, fp in enumerate(file_paths):
            wav, _ = ta.load(fp)
            all_audio.append(wav.squeeze(0))
            if i < len(file_paths) - 1:
                all_audio.append(silence)
        
        final_wav = torch.cat(all_audio, dim = -1)
        ta.save(output_dir, final_wav.unsqueeze(0), model.sr)
        shutil.rmtree(temp_dir, ignore_errors = True)
        return output_dir

    def merge_voice_with_music(self, music_path: str, tts_path: str, output_path: str):
        music = AudioFileClip(music_path)
        tts = AudioFileClip(tts_path)

        if tts.duration > music.duration:
            music = music.with_effects([afx.AudioLoop(duration=tts.duration)])
        
        music = music.with_effects([afx.MultiplyVolume(AudioMaker.MUSIC_VOLUME)])
        tts = tts.with_effects([afx.MultiplyVolume(AudioMaker.TTS_VOLUME)])
        start_time = random.uniform(0, music.duration - tts.duration)
        music_segment = music.subclipped(start_time, start_time + tts.duration)
        final_clip = CompositeAudioClip([tts, music_segment])
        final_clip.write_audiofile(output_path, fps=44100)
        return output_path, tts.duration

if __name__ == "__main__":
    audio = AudioMaker()
    txt = """
    The Airbus A380 is the largest passenger airplane in the world. It’s a double-decker jet that can carry up to 853 passengers in an all-economy layout, though most airlines use it for around 500 to 550 people in multiple classes.
    The plane is 73 meters long, has a wingspan of nearly 80 meters, and weighs about 560 tons when fully loaded. It’s powered by four massive engines, each producing up to 70,000 pounds of thrust. The A380 can fly 15,000 kilometers nonstop, enough to connect cities like Dubai to Los Angeles or Sydney to London without refueling.
    Inside, it’s quiet and spacious — some airlines even installed showers, bars, and lounges. Despite its engineering brilliance, it was too large and expensive for many routes, so production ended in 2021. Still, it remains a symbol of how far human aviation has come — a flying giant that turned the sky into a two-story highway.
    """
    out = audio.create_tts(txt, "en", "data/voices/zuzia.wav", "out_temp.wav")
    x = audio.merge_voice_with_music("data/music/background_music.mp3", "out_temp.wav", "xd.mp3")
    print(x)
