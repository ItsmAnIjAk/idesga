import datetime
import requests
import os
import re
import pytube
import subprocess
from pytube import YouTube
import streamlit as st
from PIL import Image
from io import BytesIO

def getVideo(url): #Check to ensure that the video can be found
    global video_found, video
    try:
        video = YouTube(url)
        video_found = True
    except pytube.exceptions.RegexMatchError:
        st.error('Invalid URL.')
        video_found = False
    except pytube.exceptions.VideoUnavailable:
        st.error('Video nije dostupan.')
        video_found = False
    return video

def loadThumbnail(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    return img

@st.cache
def getStats(video): # Return the formated video stats
    header = (f'**{video.title}**' 
            + f' *By: {video.author}*')
    thumbnail = loadThumbnail(video.thumbnail_url)
    info = (f'Trajanje: **{datetime.timedelta(seconds = video.length)}** \n'
          + f'Pregledi: **{video.views:,}**')
    return header, thumbnail, info

st.title('YouTube Downloader')

url = st.text_input('Upisi URL Videa')

if url:
    video = getVideo(url)
    if video_found:
        header, thumbnail, info = getStats(video)
        st.header(header)
        st.image(thumbnail, width = 750)
        st.write(info)
        download_type = st.radio(
        'Odaberi nacin: ', [
        'Video i Audio (.mkv)', 
        'Samo Audio (.mp3)', 
        'Samo Video (.mp4)']
        )

        if download_type == 'Video i Audio (.mkv)':
            video_stream = video.streams.filter(type = 'video', subtype = '.mp4').order_by(attribute_name = 'resolution').last()
            audio_stream = video.streams.get_audio_only()
            filesize = round((video_stream.filesize + audio_stream.filesize)/1000000, 2)
            if st.button(f'Instaliraj (~{filesize} MB)'): 
            # To get the highest resolution, the audio and video streams must be installed seperate as .mp4s,
            # so the audio track must be converted to an mp3, then merged with the video, then the other files must be deleted
                with st.spinner(
                 f'Instaliranje {video.title}... ***Ne otvarajte fajlove pre nego sto se instaliraju!***'
                ):
                    video_stream.download(filename = 'video-track')
                    audio_stream.download(filename = 'audio-track')
                    convert_mp3 = 'ffmpeg -i audio-track.mp4 audio-track.mp3'
                    subprocess.run(convert_mp3, shell = True)
                    os.remove('audio-track.mp4')
                    formatted_title = re.sub("[^0-9a-zA-Z]+", "-", video.title)
                    merge_audio_video = (
                                         'ffmpeg -y -i audio-track.mp3 '
                                         '-r 30 -i video-track.mp4 '
                                         '-filter:a aresample=async=1 -c:a flac -c:v '
                                        f'copy Downloads/{formatted_title}.mkv'
                                          )
                    subprocess.run(merge_audio_video, shell = True)
                    os.remove('audio-track.mp3')
                    os.remove('video-track.mp4')
                st.success(f'Zavrseno Instaliranje {video.title}!')

        if download_type == 'Samo Audio (.mp3)':
            stream = video.streams.get_audio_only()
            filesize = round(stream.filesize/1000000, 2)
            if st.button(f'Instaliraj (~{filesize} MB)'):
                with st.spinner(
                 f'Instaliranje {video.title}... ***Ne otvarajte fajlove pre nego sto se instaliraju!***'
                ):
                    stream.download(filename = 'audio')
                    convert_mp3 = f'ffmpeg -i audio.mp4 Downloads/{re.sub("[^0-9a-zA-Z]+", "-", video.title)}.mp3'
                    subprocess.run(convert_mp3, shell = True)
                    os.remove('Downloads/audio.mp4')
                st.success(f'Zavrseno Instaliranje {video.title}!')

        if download_type == 'Samo Video (.mp4)':
            stream = video.streams.filter(type = 'video', subtype = '.mp4').order_by(attribute_name = 'resolution').last()
            filesize = round(stream.filesize/1000000, 2)
            if st.button(f'Instaliraj (~{filesize} MB)'):
                with st.spinner(
                 f'Instaliranje {video.title}... ***Ne otvarajte fajlove pre nego sto se instaliraju!***'
                ):
                    stream.download(filename = video.title + ' Video Only', output_path = 'Downloads')
                st.success(f'Zavrseno Instaliranje {video.title}!')
