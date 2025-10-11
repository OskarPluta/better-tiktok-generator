import ffmpeg 
import whisper
import time 
import os
import random
import json

from utils import *

class Transcriber:
    def __init__(self, font_path: str, watermark_text: str = " ", model: str = "base", device: str = "cuda"):
        self.font_path = font_path
        self.watermark_text = watermark_text
        self.model = whisper.load_model(model, device=device)

    def transcribe(self, video_path):
        transcription = self.model.transcribe(video_path, word_timestamps=True, fp16=False)

        return transcription
    
    def get_watrmark_filter(self, text):
        return (
        f"drawtext=text='{Transcriber.normalize_text(self.watermark_text)}':"
        f"fontfile='{self.font_path}':"
        "fontcolor=white:fontsize=48:"
        "x=w-text_w-10:y=h-text_h-10:"
        "shadowx=2:shadowy=2:shadowcolor=black:"
        "borderw=2:bordercolor=black:"
        "enable='1'"
        )

    def add_subtitles(self, video_path, output_path, transcription_fixed):
        filter = []
        for segment in transcription_fixed:
            print(segment)
            start_time = segment['start']
            end_time = segment['end']
            word = Transcriber.normalize_text(segment['word'])
            filter_text = (
                    f"drawtext=text='{word}':"
                    f"fontfile='{self.font_path}':"
                    f"fontcolor={Transcriber.get_color()}:fontsize=72:"
                    "x=(w-text_w)/2:y=(h-text_h)/2:"
                    "shadowx=3:shadowy=3:shadowcolor=black:"
                    "borderw=3:bordercolor=black:"
                    f"enable='between(t,{start_time},{end_time})'"
            )
            filter.append(filter_text)
        filter.append(self.get_watrmark_filter(self.watermark_text))
        vf = ",".join(filter)
        (
        ffmpeg
        .input(video_path)
        .output(
            output_path,
            vf=vf,
            vcodec='h264_nvenc',
            acodec='copy',
            preset='p6',
            profile='high',
            tune='hq',
            rc_lookahead=8,
            bf=2,
            rc='vbr',
            cq=26,
            b='0',
            maxrate='120M',
            bufsize='240M'
        )
        .run(overwrite_output=True)  # Overwrite the output file if it exists
        )

    @staticmethod
    def get_color():
        return random.choices(["white", "yellow", "red"], [4, 1, 1])[0]
    @staticmethod
    def normalize_text(t):
        return t\
        .replace("\\", "\\\\")\
        .replace('"', '""')\
        .replace("'", "''")\
        .replace("%", "\\%")\
        .replace(":", "\\:")  

if __name__ == "__main__":
    org = """
    The Airbus A380 is the largest passenger airplane in the world. It’s a double-decker jet that can carry up to 853 passengers in an all-economy layout, though most airlines use it for around 500 to 550 people in multiple classes.
    The plane is 73 meters long, has a wingspan of nearly 80 meters, and weighs about 560 tons when fully loaded. It’s powered by four massive engines, each producing up to 70,000 pounds of thrust. The A380 can fly 15,000 kilometers nonstop, enough to connect cities like Dubai to Los Angeles or Sydney to London without refueling.
    Inside, it’s quiet and spacious — some airlines even installed showers, bars, and lounges. Despite its engineering brilliance, it was too large and expensive for many routes, so production ended in 2021. Still, it remains a symbol of how far human aviation has come — a flying giant that turned the sky into a two-story highway.
    """
    trans = Transcriber("data/fonts", model = "turbo", device="cpu")
    transcription = trans.transcribe("out_temp.wav")
    transcription = fix_transcription(org, transcription)
    print(transcription)
    trans.add_subtitles("xd.mp4", "xd_sub.mp4", transcription)
    # with open("xd.json", "w") as f:
        # json.dump(x, f, indent=2)
