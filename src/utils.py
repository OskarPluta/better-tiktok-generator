import re
import json 
import difflib
from rapidfuzz import fuzz

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

def fix_transcription(original, transcription):
    whisper_text = transcription["text"]
    segments = transcription.get("segments", [])

    # Extract words with timestamps
    words = []
    for seg in segments:
        for w in seg.get("words", []):
            words.append({
                "word": w["word"].strip(),
                "start": w["start"],
                "end": w["end"],
            })

    if not words:
        return []

    # Step 1: Find anchor points (high-confidence matches)
    anchors = []
    original_words = original.split()
    whisper_words = [w["word"] for w in words]
    
    # Use sliding window to find reliable anchors
    window_size = 3
    for i in range(len(original_words) - window_size + 1):
        orig_phrase = " ".join(original_words[i:i+window_size])
        
        for j in range(len(whisper_words) - window_size + 1):
            whisper_phrase = " ".join(whisper_words[j:j+window_size])
            
            # Use fuzzy matching for robustness
            similarity = fuzz.ratio(orig_phrase.lower(), whisper_phrase.lower())
            
            if similarity > 85:  # High confidence threshold
                anchors.append({
                    "orig_start": i,
                    "orig_end": i + window_size,
                    "whisper_start": j,
                    "whisper_end": j + window_size,
                    "time_start": words[j]["start"],
                    "time_end": words[j + window_size - 1]["end"]
                })

    # Remove overlapping anchors, keep best ones
    anchors = remove_overlapping_anchors(anchors)
    anchors.sort(key=lambda x: x["orig_start"])

    # Step 2: Interpolate between anchors
    fixed_segments = []
    orig_idx = 0

    for anchor_idx, anchor in enumerate(anchors):
        # Handle words before this anchor
        if orig_idx < anchor["orig_start"]:
            prev_time = anchors[anchor_idx - 1]["time_end"] if anchor_idx > 0 else words[0]["start"]
            next_time = anchor["time_start"]
            
            words_to_add = original_words[orig_idx:anchor["orig_start"]]
            fixed_segments.extend(
                interpolate_words(words_to_add, prev_time, next_time)
            )

        # Add anchor words with their original timestamps
        whisper_idx = anchor["whisper_start"]
        for i in range(anchor["orig_start"], anchor["orig_end"]):
            if whisper_idx < len(words):
                fixed_segments.append({
                    "word": original_words[i],
                    "start": words[whisper_idx]["start"],
                    "end": words[whisper_idx]["end"]
                })
                whisper_idx += 1

        orig_idx = anchor["orig_end"]

    # Handle remaining words after last anchor
    if orig_idx < len(original_words):
        last_time = anchors[-1]["time_end"] if anchors else words[0]["start"]
        end_time = words[-1]["end"] if words else last_time + 1
        
        words_to_add = original_words[orig_idx:]
        fixed_segments.extend(
            interpolate_words(words_to_add, last_time, end_time)
        )

    return fixed_segments


def remove_overlapping_anchors(anchors):
    """Keep non-overlapping anchors with highest similarity"""
    if not anchors:
        return []
    
    # Sort by original text position
    sorted_anchors = sorted(anchors, key=lambda x: x["orig_start"])
    result = [sorted_anchors[0]]
    
    for anchor in sorted_anchors[1:]:
        last = result[-1]
        # Check if this anchor overlaps with the last one
        if anchor["orig_start"] >= last["orig_end"] and anchor["whisper_start"] >= last["whisper_end"]:
            result.append(anchor)
    
    return result


def interpolate_words(words_list, start_time, end_time):
    """Distribute words proportionally by syllable count"""
    if not words_list:
        return []
    
    # Estimate syllable counts (simple approximation)
    syllable_counts = [max(1, len([c for c in word if c.lower() in 'aeiou'])) for word in words_list]
    total_syllables = sum(syllable_counts)
    
    duration = end_time - start_time
    result = []
    current_time = start_time
    
    for i, word in enumerate(words_list):
        syllable_duration = (syllable_counts[i] / total_syllables * duration) if total_syllables > 0 else (duration / len(words_list))
        # Ensure minimum duration
        syllable_duration = max(0.05, syllable_duration)
        
        result.append({
            "word": word,
            "start": current_time,
            "end": min(current_time + syllable_duration, end_time)
        })
        current_time += syllable_duration
    
    return result
        

if __name__ == "__main__":

    original = """
    The Airbus A380 is the largest passenger airplane in the world. It’s a double-decker jet that can carry up to 853 passengers in an all-economy layout, though most airlines use it for around 500 to 550 people in multiple classes.
    The plane is 73 meters long, has a wingspan of nearly 80 meters, and weighs about 560 tons when fully loaded. It’s powered by four massive engines, each producing up to 70,000 pounds of thrust. The A380 can fly 15,000 kilometers nonstop, enough to connect cities like Dubai to Los Angeles or Sydney to London without refueling.
    Inside, it’s quiet and spacious — some airlines even installed showers, bars, and lounges. Despite its engineering brilliance, it was too large and expensive for many routes, so production ended in 2021. Still, it remains a symbol of how far human aviation has come — a flying giant that turned the sky into a two-story highway.
    """
    with open('xd.json') as f:
        transcription = json.load(f)
    
    x = fix_transcription(original, transcription)
    print(x)