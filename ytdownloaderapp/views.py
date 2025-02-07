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
import tempfile



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
    if request.method == "GET":
        return JsonResponse({"message": "Use POST request with a YouTube URL"}, status=200)

    if request.method == "POST":
        try:
            # Get YouTube URL and format from request
            data = json.loads(request.body)
            youtube_url = data.get("youtube_url", "").strip()
            download_type = data.get("format", "merged")  # "video", "audio", "merged"

            if not youtube_url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            # Define save path
            save_path = os.path.join(settings.MEDIA_ROOT, "downloads")
            os.makedirs(save_path, exist_ok=True)

            # Download options
            ydl_opts_video = {
                'format': 'bv*[ext=mp4]',  # Best video (without audio)
                'outtmpl': os.path.join(save_path, '%(title)s_video.mp4'),
                'noplaylist': True,
            }

            ydl_opts_audio = {
                'format': 'ba',  # Best audio only
                'outtmpl': os.path.join(save_path, '%(title)s_audio.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'noplaylist': True,
            }

            ydl_opts_merged = {
                'format': 'bestvideo+bestaudio',  # Best video with audio
                'outtmpl': os.path.join(save_path, '%(title)s.mp4'),
                'noplaylist': True,
                'merge_output_format': 'mp4',  # Ensures output is in mp4 format
            }

            # Download based on user request
            if download_type == "video":
                with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                    ydl.download([youtube_url])
            elif download_type == "audio":
                with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                    ydl.download([youtube_url])
            else:  # "merged"
                with yt_dlp.YoutubeDL(ydl_opts_merged) as ydl:
                    ydl.download([youtube_url])

            # Find downloaded files
            files = os.listdir(save_path)
            video_file = next((os.path.join(save_path, f) for f in files if f.endswith("_video_only.mp4")), None)
            audio_file = next((os.path.join(save_path, f) for f in files if f.endswith(".mp3")), None)
            merged_file = next((os.path.join(save_path, f) for f in files if f.endswith(".mp4") and "_video" not in f), None)

            # Prepare response
            response_data = {"success": True}

            if download_type == "video" and video_file:
                response_data["video_only_url"] = settings.MEDIA_URL + "download/" + os.path.basename(video_file)
            elif download_type == "audio" and audio_file:
                response_data["audio_only_url"] = settings.MEDIA_URL + "download/" + os.path.basename(audio_file)
            elif download_type == "merged" and merged_file:
                response_data["merged_url"] = settings.MEDIA_URL + "download/" + os.path.basename(merged_file)
            else:
                return JsonResponse({"error": "Download failed"}, status=500)

            return JsonResponse(response_data)

        except Exception as e:
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

            # Create a temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_audio_path = os.path.join(temp_dir, "temp_audio.mp3")

                # yt-dlp options to download **audio only** as a temporary file
                ydl_opts_audio = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(temp_dir, 'temp_audio'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'noplaylist': True,
                }

                # Download audio
                with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                    ydl.download([youtube_url])

                # Ensure the file exists before proceeding
                if not os.path.exists(temp_audio_path):
                    return JsonResponse({"error": "Audio download failed"}, status=500)

                # Transcribe the audio using Whisper
                text_transcription = transcribe_audio(temp_audio_path)

            # No need to delete manually, `tempfile.TemporaryDirectory()` handles cleanup

            # Return transcribed text to frontend
            return JsonResponse({
                "success": True,
                "transcribed_text": text_transcription
            })

        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)