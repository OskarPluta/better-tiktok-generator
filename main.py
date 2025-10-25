import time

import sys
sys.path.append("src")

from audio_maker import AudioMaker
from transcriber import Transcriber
from video_maker import VideoMaker

def main():
    # start = time.time()
    # txt = """
    # Stop burning motors. Meet the phase control relay. It guards your three‑phase supply and shuts things down before damage happens.
    # If a phase is missing, the sequence is reversed, or the voltage drifts, it trips fast to protect your equipment. Watch for common clues such as uneven torque, humming contactors, or random overloads.
    # Here is how it works. The relay monitors all three phases, checks asymmetry and under or over‑voltage, and then drops the contactor on a fault.
    # Here is how to use it. Mount it before the motor starter, wire the three phases to its inputs, and route the coil through its output. Set the trip delay to about one second to ignore brief blips, and set the restart delay to a few seconds.
    # Green means healthy. Red means fault. Use it on pumps, compressors, fans, and conveyors. This small device provides big protection. A phase control relay is cheap insurance for three‑phase machines.
    # """
    # language = "en"
    # audio_maker = AudioMaker()
    # temp_wav = audio_maker.create_tts(txt, language, "data/voices/peter_griffin_1.wav", "temp/out_temp.wav")
    # temp_mp3, tts_duration = audio_maker.merge_voice_with_music("data/music/background_music.mp3", temp_wav, "temp/out_temp.mp3")
    # del audio_maker

    # video_maker = VideoMaker()
    # video_path = video_maker.make_video("temp/video.mp4", temp_mp3, multiple_backgrounds=False)
    # del video_maker

    # transcriber = Transcriber("data/fonts/fnt2.ttf", model="large", device="cpu")
    
    # result = transcriber.align_text(temp_wav, txt, language=language)
    # word_list = transcriber.result_to_word_list(result, False)

    # output_path = transcriber.add_subtitles(video_path, "output/title.mp4", word_list)
    # del transcriber

    # end = time.time()
    # print(f"Saved video in {output_path}, took {end-start} time.")

    start = time.time()
    language = "en"
    audio_maker = AudioMaker()
    conversation = [
    (0, "Phase control relays are essential for motor protection."),
    (1, "How do they work exactly?"),
    (2, "They monitor voltage and phase sequence continuously."),
    (0, "And they trip before damage occurs."),
    (1, "That makes sense. Where should I install one?"),
    (2, "Mount it before the motor starter."),
    ]

    speaker_voices = {
        0: "data/voices/peter_griffin_1.wav",
        1: "data/voices/zuzia.wav",
        2: "data/voices/kaczynski.wav"
    }

    temp_wav = audio_maker.create_conversation_tts(
        conversation=conversation,
        language=language,
        speaker_wavs=speaker_voices,
        output_dir="temp/conversation_temp.wav"
    )
    temp_mp3, tts_duration = audio_maker.merge_voice_with_music(
        "data/music/background_music.mp3", 
        temp_wav, 
        "temp/out_temp.mp3"
    )
    del audio_maker


    # video_maker = VideoMaker()
    # video_path = video_maker.make_video("temp/video.mp4", temp_mp3, multiple_backgrounds=False)
    # del video_maker

    # transcriber = Transcriber("data/fonts/fnt2.ttf", model="large", device="cpu")
    
    # result = transcriber.align_text(temp_wav, txt, language=language)
    # word_list = transcriber.result_to_word_list(result, False)

    # output_path = transcriber.add_subtitles(video_path, "output/title.mp4", word_list)
    # del transcriber

    # end = time.time()
    # print(f"Saved video in {output_path}, took {end-start} time.")


if __name__ == "__main__":
    main()