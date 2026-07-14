# Better TikTok Generator

A Python toolkit for building narrated, vertical short-form videos from local media. It combines multilingual voice cloning, background music, a randomly selected video background, word-level text alignment, animated subtitles, and optional character background removal.

## What it does

The intended pipeline is:

```text
script + reference voices
          |
          v
multilingual TTS -----> narration WAV
                           |
background music ----------+-----> mixed MP3
                                      |
background video ---------------------+-----> 1080x1920 video
                                                |
script + stable-ts word alignment --------------+-----> subtitled MP4
```

The repository currently provides:

- Single-speaker and multi-speaker TTS helpers using Chatterbox Multilingual (the active multi-speaker path is the usable example today).
- Sentence-aware chunking for longer text.
- Per-speaker RMS normalization and configurable pauses between conversation turns.
- Voice/music mixing with automatic music looping and a random music start point.
- Random background-video selection, center-cropping to 9:16, and export at 1080x1920 and 60 fps.
- Forced alignment of a known script to generated audio with stable-ts/Whisper.
- Short, animated, burned-in subtitle groups and an optional watermark.
- Batch image background removal with BiRefNet.

## Project status

`main.py` contains two examples:

- The active example creates a three-speaker conversation, writes it to `temp/conversation_temp.wav`, and mixes it with music as `temp/out_temp.mp3`.
- A single-narrator, full-video example is retained as commented code and still needs cleanup before it can run end to end.

There is no CLI, configuration file, test suite, or bundled media. Input assets and generated media are intentionally ignored by Git. The Python environment itself is reproducible and its complete import path has been verified with the checked-in lockfile.

## Requirements

- Python 3.11 (the version pinned in `.python-version` and required by `pyproject.toml`).
- [uv](https://docs.astral.sh/uv/) for installing the exact environment from `uv.lock`.
- The FFmpeg executable must be installed and available on `PATH`. The Python package `ffmpeg-python` does not install the executable. Subtitle rendering also requires an FFmpeg build with the `drawtext` filter.
- Internet access and enough disk space for the Chatterbox, Whisper, and BiRefNet model downloads on first use.
- A CUDA-capable GPU is optional. The active audio and background-removal code currently selects CPU explicitly, so GPU use requires changing the relevant `device` values.

Install FFmpeg on Ubuntu/Debian, for example:

```bash
sudo apt update
sudo apt install ffmpeg
ffmpeg -version
```

## Installation

Clone the repository and install the locked environment:

```bash
git clone https://github.com/OskarPluta/better-tiktok-generator.git
cd better-tiktok-generator
uv sync --frozen
```

That single command installs Chatterbox, Transformers, and a mutually compatible PyTorch stack from `uv.lock`. The project intentionally uses Python 3.11 with Torch 2.6, Torchaudio 2.6, and Torchvision 0.21 because these versions satisfy Chatterbox's runtime requirements.

Verify the environment without downloading any AI model weights:

```bash
uv run python -c "import chatterbox, torch, torchaudio, torchvision, transformers; print(torch.__version__)"
```

The expected Torch version is `2.6.0`. FFmpeg remains a system dependency and is not installed by uv.

## Asset layout

Create the working directories first:

```bash
mkdir -p data/voices data/music data/videos/long data/videos/short \
  data/fonts data/characters data/characters_without_background temp output
```

Populate them using this layout, or update the hard-coded paths in `main.py`:

```text
data/
├── voices/
│   ├── peter_griffin_1.wav       # reference voice for speaker 0
│   ├── zuzia.wav                 # reference voice for speaker 1
│   └── kaczynski.wav             # reference voice for speaker 2
├── music/
│   └── background_music.mp3
├── videos/
│   ├── long/                     # background clips currently used
│   │   └── background.mp4
│   └── short/                    # discovered, but not yet used
├── fonts/
│   └── fnt2.ttf                  # used by FFmpeg subtitles/watermark
├── characters/                   # source images for background removal
└── characters_without_background/ # generated transparent PNGs

temp/                             # intermediate audio/video
output/                           # final videos
```

A clear reference recording with one speaker and little background noise generally gives the TTS model better material to imitate.

## Quick start: conversation audio

Edit the conversation and voice paths in `main.py`:

```python
conversation = [
    (0, "Phase control relays are essential for motor protection."),
    (1, "How do they work exactly?"),
]

speaker_voices = {
    0: "data/voices/speaker_0.wav",
    1: "data/voices/speaker_1.wav",
}
```

Speaker IDs in `conversation` must have matching entries in `speaker_voices`. Set `language` to a language ID supported by the installed Chatterbox Multilingual model, such as `"en"` or `"pl"`.

Run the active example from the repository root:

```bash
uv run python main.py
```

Expected outputs:

```text
temp/conversation_temp.wav
temp/out_temp.mp3
```

Model initialization and audio generation can take a while on CPU, especially on the first run.

### Generate a multi-speaker track

```python
from audio_maker import AudioMaker

audio_maker = AudioMaker()
narration_path = audio_maker.create_conversation_tts(
    conversation=[
        (0, "Welcome to the channel."),
        (1, "Today we are explaining phase control relays."),
    ],
    language="en",
    speaker_wavs={
        0: "data/voices/speaker_0.wav",
        1: "data/voices/speaker_1.wav",
    },
    output_dir="temp/conversation.wav",
    pause_duration=0.3,
    target_rms=0.1,
)

mixed_path, narration_duration = audio_maker.merge_voice_with_music(
    music_path="data/music/background_music.mp3",
    tts_path=narration_path,
    output_path="temp/mixed.mp3",
)
```

Extra keyword arguments passed to `create_conversation_tts` override the generation defaults (`exaggeration`, `cfg_weight`, `temperature`, `repetition_penalty`, `min_p`, and `top_p`). The music and voice volumes are class constants:

```python
AudioMaker.MUSIC_VOLUME = 0.05
AudioMaker.TTS_VOLUME = 1.0
AudioMaker.device = "cpu"  # change to "cuda" when supported by the environment
```

### Create a vertical background video

```python
from video_maker import VideoMaker

video_maker = VideoMaker(videos_path="data/videos")
video_path = video_maker.make_video(
    output_path="temp/video.mp4",
    audio_path="temp/mixed.mp3",
    multiple_backgrounds=False,
)
```

The implementation chooses one file from `data/videos/long`, takes a random excerpt, center-crops it to 9:16, resizes it to 1080x1920, and attaches the narration. Use a background clip that is at least one second longer than the narration; the current random-range and subclip logic requires that margin.

`multiple_backgrounds=True` is not implemented yet.

### Align text and burn in subtitles

```python
from transcriber import Transcriber

script = "Welcome to the channel. Today we are explaining phase control relays."

transcriber = Transcriber(
    font_path="data/fonts/fnt2.ttf",
    watermark_text="@your_handle",
    model="turbo",
    device="cpu",
)
result = transcriber.align_text(
    audio_path="temp/conversation.wav",
    correct_text=script,
    language="en",
)
words = transcriber.result_to_word_list(result, replace_polish_chars=False)
transcriber.add_subtitles(
    video_path="temp/video.mp4",
    output_path="output/final.mp4",
    word_list=words,
)
```

### Remove image backgrounds in bulk

Place images anywhere under `data/characters`, then run:

```bash
uv run python src/background_removal.py
```

The script recursively processes JPG, JPEG, PNG, BMP, and WebP files with `zhengpeng7/BiRefNet`. It preserves subdirectories, writes transparent PNGs under `data/characters_without_background`, and skips outputs that already exist. It downloads model code with `trust_remote_code=True`; review and pin remote model code before using this in a security-sensitive environment.
