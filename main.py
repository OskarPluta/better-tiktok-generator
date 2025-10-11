import re
import torch
import os 
import shutil

import torchaudio as ta

from chatterbox.tts import ChatterboxTTS
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

def chunk_text(text, max_len=500):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) < max_len:
            current += " " + sent
        else:
            chunks.append(current.strip())
            current = sent
    if current:
        chunks.append(current.strip())
    return chunks


with open("sejm.txt", "r") as f:
    PROMPT = f.read()

device = "cpu"

output_path = "out_tusk.wav"

model = ChatterboxMultilingualTTS.from_pretrained(device=device)
temp_dir = "./temp_audio"
print(model.sr)
if os.path.exists(temp_dir):
    shutil.rmtree(temp_dir)
os.makedirs(temp_dir)

chunks = chunk_text(PROMPT, max_len=500)


file_paths = []
for i, chunk in enumerate(chunks):
    print(i)
    wav_chunk = model.generate(chunk, language_id="pl", audio_prompt_path="glosy/tusk.wav", exaggeration=0.5, cfg_weight=0.5, temperature=0.6)
    file_path = os.path.join(temp_dir, f"chunk_{i}.wav")
    ta.save(file_path, wav_chunk, model.sr)
    file_paths.append(file_path)
    
    del wav_chunk

silence_duration = 0.2
silence = torch.zeros(int(model.sr * silence_duration))
print(model.sr)
all_audio = []
for i, fp in enumerate(file_paths):
    wav, _ = ta.load(fp)
    all_audio.append(wav.squeeze(0))
    if i < len(file_paths) -1:
        all_audio.append(silence)
    
final_wav = torch.cat(all_audio, dim=-1)
ta.save(output_path, final_wav.unsqueeze(0), model.sr)

shutil.rmtree(temp_dir, ignore_errors=True)

