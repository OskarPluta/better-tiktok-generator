import os
import random

from moviepy import AudioFileClip, VideoFileClip

class VideoMaker:

    def __init__(self, videos_path: str = "data/videos"):
        self.videos_path = videos_path

    def get_all_video_files(self):
        short_videos = []
        long_videos = []
        for root, _, files in os.walk(self.videos_path+"/short"):
            for file in files:
                if file.endswith(('mp4', 'mov', 'avi', 'mkv')):
                    short_videos.append(os.path.join(root, file))

        for root, _, files in os.walk(self.videos_path+"/long"):
            for file in files:
                if file.endswith(('mp4', 'mov', 'avi', 'mkv')):
                    long_videos.append(os.path.join(root, file))

        return short_videos, long_videos
    
    def make_video(self, output_path: str, audio_path: str, multiple_backgrounds: bool):
        if multiple_backgrounds:
            # video_path = self.video_from_longer_background()
            pass
        else:
            self.video_from_longer_background(audio_path=audio_path, output_path=output_path)

        return output_path 


    def video_from_longer_background(self, audio_path, output_path):
        short_videos, long_videos = self.get_all_video_files()

        if long_videos == []:
            raise ValueError(f"No long videos inside path {self.videos_path}")
        
        audio = AudioFileClip(audio_path)
        random_video_path = random.choice(long_videos)
        clip = VideoFileClip(random_video_path, audio=False, fps_source='tbr')
        if clip.duration < audio.duration:
            raise ValueError(f"One of the long videos is shorter than the audio created! Consider moving it to short videos. {random_video_path}")

        original_width, original_height = clip.size
        target_aspect_ratio = 9 / 16
        target_width = original_width
        target_height = original_width / target_aspect_ratio

        if target_height > original_height:
            target_height = original_height
            target_width = original_height * target_aspect_ratio
        
        x_center = original_width // 2
        y_center = original_height // 2

        crop_x1 = x_center - (target_width // 2)
        crop_x2 = x_center + (target_width // 2)
        crop_y1 = y_center - (target_height // 2)
        crop_y2 = y_center + (target_height // 2)

        clip = clip.cropped(x1=crop_x1, x2=crop_x2, y1=crop_y1, y2=crop_y2)
        clip = clip.resized((1080, 1920))
        start = random.randint(0, int(clip.duration - audio.duration) - 1)
        clip = clip.subclipped(start, start + audio.duration + 1).with_audio(audio)
        clip.write_videofile(output_path, fps=60)

    def paste_character(img_path, timestamp):
        pass
        

       
if __name__ == "__main__":
    video = VideoMaker()
    video.make_video("xd.mp4", "xd.mp3", multiple_backgrounds=False)