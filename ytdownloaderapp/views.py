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

import os
import json
import yt_dlp
from django.http import JsonResponse, FileResponse
from django.conf import settings

import json
import yt_dlp
import os
import tempfile
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def yt_download(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            youtube_url = data.get("youtube_url", "").strip()
            download_type = data.get("format", "merged")

            if not youtube_url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            file_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

            # Set download options
            if download_type == "merged":  # Video + Audio
                ydl_opts = {
                    "format": "bestvideo+bestaudio",
                    "outtmpl": file_template,
                    "merge_output_format": "mp4",
                    "postprocessors": [
                        {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
                        {"key": "FFmpegEmbedSubtitle"},
                    ],
                }
            elif download_type == "video":  # Video Only
                ydl_opts = {
                    "format": "bestvideo[ext=mp4]/bestvideo",
                    "outtmpl": file_template,
                }
            elif download_type == "audio":  # Audio Only
                ydl_opts = {
                    "format": "bestaudio",
                    "outtmpl": file_template,
                    "postprocessors": [
                        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
                    ],
                }
            else:
                return JsonResponse({"error": "Invalid format type"}, status=400)

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                filename = ydl.prepare_filename(info)

            # Fix file extension
            if download_type == "merged":
                filename = filename.rsplit(".", 1)[0] + ".mp4"
            elif download_type == "audio":
                filename = filename.rsplit(".", 1)[0] + ".mp3"

            # Open file for streaming
            response = FileResponse(open(filename, "rb"), as_attachment=True, filename=os.path.basename(filename))

            # Delete file after response is sent
            response["File-Path"] = filename  # Custom header to track the file for deletion

            def delete_file(request, response):
                try:
                    os.remove(response["File-Path"])
                    os.rmdir(temp_dir)  # Remove temp directory if empty
                except Exception as e:
                    print(f"Error deleting file: {e}")

            response.close = lambda: delete_file(request, response)  # Hook delete after response closes

            return response

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)





import json
import yt_dlp
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def fetch_video_details(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            youtube_url = data.get("youtube_url", "").strip()

            if not youtube_url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            ydl_opts = {
                "quiet": True,
                "skip_download": True,
                "extract_flat": False,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)

            video_data = {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration_string"),  # Get duration in HH:MM:SS format
            }

            return JsonResponse(video_data)

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