import ffmpeg 
import stable_whisper
import random


class Transcriber:
    def __init__(self, font_path: str, watermark_text: str = " ", model: str = "turbo", device: str = "cuda"):
        self.font_path = font_path
        self.watermark_text = watermark_text
        self.model = stable_whisper.load_model(model, device=device)


    def align_text(self, audio_path: str, correct_text: str, language: str = "en"):
        """
        Align correct text with audio using stable-whisper's built-in alignment.
        """
        result = self.model.align(audio_path, correct_text, language=language, token_step = 400)
        result.adjust_gaps()
        # print(result)
        return result
    

    def result_to_word_list(self, result, replace_polish_chars=False):
        """Convert WhisperResult to list of word dictionaries for subtitle rendering"""
        words = []
        for segment in result.segments:
            for word in segment.words:
                if not replace_polish_chars:
                    words.append({
                        'word': word.word.strip(),
                        'start': word.start,
                        'end': word.end
                    })
                else:
                    replacements = {
                        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l',
                        'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L',
                        'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
                    }
                    word.word = word.word.strip()
                    word.word = ''.join(replacements.get(c, c) for c in word.word)
                    words.append({
                        'word': word.word,
                        'start': word.start,
                        'end': word.end
                    })
        return words
    
    def group_words(self, word_list, min_duration=0.6, max_group_duration=1.0, max_length=18):
        """Group words into subtitle segments based on duration, length and sentence boundaries"""
        grouped = []
        current_group = None

        for word_data in word_list:
            word = word_data['word']
            word_duration = word_data['end'] - word_data['start']
            ends_sentence = word.rstrip().endswith(('.', '!', '?'))

            if current_group is None:
                current_group = {
                    'text': word,
                    'start': word_data['start'],
                    'end': word_data['end']
                }
            else:
                potential_duration = word_data['end'] - current_group['start']
                potential_text = current_group['text'] + ' ' + word
                
                # Check if adding this word would exceed max length
                would_exceed_length = len(potential_text) > max_length
                
                if (word_duration < min_duration and 
                    potential_duration <= max_group_duration and 
                    not would_exceed_length):
                    current_group['text'] += ' ' + word
                    current_group['end'] = word_data['end']
                else:
                    grouped.append(current_group)
                    current_group = {
                        'text': word,
                        'start': word_data['start'],
                        'end': word_data['end']
                    }
                    
            if ends_sentence and current_group is not None:
                grouped.append(current_group)
                current_group = None
                
        if current_group is not None:
            grouped.append(current_group)

        return grouped


    def _get_watermark_filter(self):
        return (
            f"drawtext=text='{Transcriber.normalize_text(self.watermark_text)}':"
            f"fontfile='{self.font_path}':"
            "fontcolor=white:fontsize=48:"
            "x=w-text_w-10:y=h-text_h-10:"
            "shadowx=2:shadowy=2:shadowcolor=black:"
            "borderw=2:bordercolor=black:"
            "enable='1'"
        )
    
    def _get_text_filter(self, text, start_time, end_time):
        # Animation duration in seconds
        animation_duration = 0.05
        min_size = 40
        max_size = 82
        
        filter_text = (
            f"drawtext=text='{text}':"
            f"fontfile='{self.font_path}':"
            "fontcolor=white:"
            f"fontsize='min({min_size}+({max_size-min_size}*(t-{start_time})/{animation_duration}),{max_size})':"
            "x=(w-text_w)/2:y=(h-text_h)/2:"
            "shadowx=7:shadowy=7:shadowcolor=black:"
            "borderw=10:bordercolor=black:"
            f"enable='between(t,{start_time},{end_time})'"
        )
        return filter_text



    def add_subtitles(self, video_path, output_path, word_list):
        """Adds subtitles to the video"""
        filter = []
        grouped = self.group_words(word_list)
        for segment in grouped:
            start_time = segment['start']
            end_time = segment['end']
            word = Transcriber.normalize_text(segment['text'])
            text_filter = self._get_text_filter(word, start_time, end_time)
            filter.append(text_filter)

        filter.append(self._get_watermark_filter(self.watermark_text))
        vf = ",".join(filter)
        
        (
            ffmpeg
            .input(video_path)
            .output(
                output_path,
                vf=vf,
                # vcodec='h264_nvenc',
                vcoded='libx264',
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
            .run(overwrite_output=True)
        )
        return output_path
    
    def normalize_text(t):
        return t\
            .replace("\\", "\\\\")\
            .replace('"', '""')\
            .replace("'", "''")\
            .replace("%", "\\%")\
            .replace(":", "\\:")\
            .replace("—", "")


if __name__ == "__main__":
    org = """
    The Airbus A380 is the largest passenger airplane in the world. It's a double-decker jet that can carry up to 853 passengers in an all-economy layout, though most airlines use it for around 500 to 550 people in multiple classes.
    The plane is 73 meters long, has a wingspan of nearly 80 meters, and weighs about 560 tons when fully loaded. It's powered by four massive engines, each producing up to 70,000 pounds of thrust. The A380 can fly 15,000 kilometers nonstop, enough to connect cities like Dubai to Los Angeles or Sydney to London without refueling.
    Inside, it's quiet and spacious — some airlines even installed showers, bars, and lounges. Despite its engineering brilliance, it was too large and expensive for many routes, so production ended in 2021. Still, it remains a symbol of how far human aviation has come — a flying giant that turned the sky into a two-story highway.
    """
    trans = Transcriber("data/fonts/fnt2.ttf", model="large", device="cpu")
    result = trans.align_text("out_temp.wav", org, language="en")
    word_list = trans.result_to_word_list(result)
    print(f"Aligned {len(word_list)} words")
    print(word_list[:5])
    trans.add_subtitles("xd.mp4", "xd_sub.mp4", word_list)
