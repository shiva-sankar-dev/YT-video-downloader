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

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import yt_dlp

@csrf_exempt
def yt_download(request):
    if request.method == "GET":
        return JsonResponse({"message": "Use POST request with a YouTube URL"}, status=200)

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            youtube_url = data.get("youtube_url", "").strip()
            download_type = data.get("format", "merged")  # "video", "audio", "merged"
            # print(download_type,"________________________")

            if not youtube_url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            # Define extraction options to get the direct URL instead of downloading
            ydl_opts = {
                'format': 'best' if download_type == "merged" else
                          'bv*[ext=mp4][protocol^=http]/b' if download_type == "video" else
                          'ba',  # best audio
                'quiet': True,  # Suppresses unnecessary logs
                'noplaylist': True,
                'extract_flat': False,
                'force_generic_extractor': False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)  # Fetch video details without downloading
                
                if not info:
                    return JsonResponse({"error": "Failed to retrieve video info"}, status=500)
                
                # Get the best format URL
                download_url = info.get("url", None)
                if not download_url:
                    return JsonResponse({"error": "Download URL not found"}, status=500)

                return JsonResponse({"success": True, "download_url": download_url})

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