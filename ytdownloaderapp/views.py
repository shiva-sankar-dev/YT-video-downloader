from django.shortcuts import render
from pytube import YouTube
import os
import json
import yt_dlp
import subprocess
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import whisper




# def transcribe_audio(audio_file_path):
#     model = whisper.load_model("base")
#     result = model.transcribe(audio_file_path)
#     return result['text']


def index(request):

    return render(request, "index.html")


from yt_dlp import YoutubeDL

from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token

def get_csrf_token(request):
    return JsonResponse({'csrfToken': get_token(request)}) 

@csrf_exempt
def yt_download(request):
    print("hello world")

    if request.method == "GET":
        return JsonResponse({"message": "Use POST request with a YouTube URL"}, status=200)

    if request.method == "POST":
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        try:
            # Get YouTube URL from request
            data = json.loads(request.body)
            youtube_url = data.get("youtube_url", "").strip()
            if not youtube_url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            # Define save path
            save_path = os.path.join(settings.MEDIA_ROOT, "download")
            os.makedirs(save_path, exist_ok=True)

            # yt-dlp options to download video **without audio**
            ydl_opts_video = {
                'format': 'bv*[ext=mp4]',  # **Only best video, no audio**
                'outtmpl': os.path.join(save_path, '%(title)s_video.mp4'),
                'noplaylist': True,
            }

            # yt-dlp options to download **audio only**
            ydl_opts_audio = {
                'format': 'ba',  # **Only best audio**
                'outtmpl': os.path.join(save_path, '%(title)s_audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',  # Convert to MP3
                    'preferredquality': '192',  # Good quality
                }],
                'noplaylist': True,
            }

            # Download video (without audio)
            with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                ydl.download([youtube_url])

            # Download audio
            with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                ydl.download([youtube_url])

            # Find downloaded files
            files = os.listdir(save_path)
            video_file = next((os.path.join(save_path, f) for f in files if f.endswith("_video.mp4")), None)
            audio_file = next((os.path.join(save_path, f) for f in files if f.endswith(".mp3")), None)

            if not video_file or not audio_file:
                return JsonResponse({"error": "Video or audio download failed"}, status=500)

            # Create merged file path
            base_name = os.path.splitext(os.path.basename(video_file))[0].replace("_video", "")  # Remove suffix
            merged_file = os.path.join(save_path, f"{base_name}_merged.mp4")

            # Merge video and audio using ffmpeg
            merge_command = [
                "ffmpeg", "-i", video_file, "-i", audio_file,
                "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
                "-strict", "experimental", merged_file
            ]
            subprocess.run(merge_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Check if merged file was created
            if not os.path.exists(merged_file):
                return JsonResponse({"error": "Merging failed"}, status=500)

            # Return URLs
            return JsonResponse({
                "success": True,
                "video_only_url": settings.MEDIA_URL + "download/" + os.path.basename(video_file),  # Video without audio
                "audio_only_url": settings.MEDIA_URL + "download/" + os.path.basename(audio_file),  # Audio only
                "merged_url": settings.MEDIA_URL + "download/" + os.path.basename(merged_file)  # Video + Audio merged
            })

        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

def transcribe_audio(audio_file_path):
    model = whisper.load_model("base")  # Load Whisper model
    result = model.transcribe(audio_file_path)
    return result['text']

@csrf_exempt
def yt_download_script(request):
    if request.method == "POST":
        try:
            # Get YouTube URL from request
            data = json.loads(request.body)
            youtube_url = data.get("youtube_url", "").strip()
            if not youtube_url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            # Define save path
            save_path = os.path.join(settings.MEDIA_ROOT, "download")
            os.makedirs(save_path, exist_ok=True)

            # yt-dlp options to download **audio only**
            ydl_opts_audio = {
                'format': 'ba',  # **Only best audio**
                'outtmpl': os.path.join(save_path, '%(title)s_audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',  # Convert to MP3
                    'preferredquality': '192',  # Good quality
                }],
                'noplaylist': True,
            }

            # Download audio
            with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                ydl.download([youtube_url])

            # Find the downloaded audio file
            files = os.listdir(save_path)
            audio_file = next((os.path.join(save_path, f) for f in files if f.endswith(".mp3")), None)

            if not audio_file:
                return JsonResponse({"error": "Audio download failed"}, status=500)

            # Transcribe the audio using Whisper
            text_transcription = transcribe_audio(audio_file)

            # Return transcribed text to frontend
            return JsonResponse({
                "success": True,
                "transcribed_text": text_transcription
            })

        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)