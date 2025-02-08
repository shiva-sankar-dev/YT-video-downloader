from django.urls import path
from .views import *
urlpatterns = [
    path('index/', index, name="index"),
    path('yt_download/', yt_download,name="yt_download"),
    path('fetch_video_details/', fetch_video_details,name="yt_download"),
    path('yt_download_script/', yt_download_script,name="yt_download_script"),
    path('get_csrf/', get_csrf_token, name='get_csrf'),
]
