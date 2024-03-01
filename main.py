import sys

import fitz  # PyMuPDF
import subprocess
from subprocess import Popen, PIPE
import os

## Util
def get_video_dimensions(video):
    """returns (width, height)"""
    command = [
        "ffprobe", 
        '-v', 'error',
        '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height',
        '-of', 'csv=s=x:p=0',
        video
    ]
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    return [int(x) for x in stdout.decode().strip("\n").strip("\r").split("x")]

def resize(video, new_h=None, new_w=None):
    if new_h is None and new_w is None:
        return 
    if new_w is None:
        command = [
            'ffmpeg',
            '-i', video,  # Input format
            '-filter:v', 'scale="trunc(oh*a/2)*2:'+str(new_h)+'"',
            '-y',
            '-c:a', 'copy',
            video
        ]
    elif new_h is None:
        command = [
            'ffmpeg',
            '-i', video,  # Input format
            '-filter:v', 'scale="'+str(new_w)+':trunc(ow/a/2)*2"',
            '-y',
            '-c:a', 'copy',
            video
        ]
    print(command)
    subprocess.run(command)

#print(get_video_dimensions("shrunk.mp4"))
#resize("shrunk.mp4", new_h=1440)
#print(get_video_dimensions("shrunk.mp4"))
#sys.exit()

def combine_videos(videos, output_video):
    with open("slide_videos.txt", "w") as f:
        for v in videos:
            f.write(f"file {v}\n")
    command = [
        'ffmpeg',
        '-f', 'concat',
        '-i', "slide_videos.txt",  # Input format
        '-y',
        '-c', 'copy',
        output_video
    ]

    subprocess.run(command)

def loop_video(n, video, outname):
    videos = [video]*n
    combine_videos(videos, outname)

def get_durations():
    lines = None
    with open("slide_durations.txt", "r") as f:
        lines = f.readlines()[0]
    if lines is None:
        print("fucked it mate")
    return [int(x) for x in lines.strip("\n").split(",")]

def pdf_to_png(pdf_file):
    # Open the PDF file
    doc = fitz.open(pdf_file)
    filenames = []
    # Iterate through each page
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # number of page
        pix = page.get_pixmap()
        if page_num < 10:
            output_file = f"page_{page_num}.png"
        else:
            output_file = f"page_{page_num}.png"
        filenames.append(output_file)
        pix.save(output_file)

    doc.close()
    return filenames

def convert_image_to_video(image_name, video_name, duration_s):
    command = [
        'ffmpeg',
        '-framerate', str(1/duration_s),
        '-i', image_name,  # Input format
        '-loop', '1',
        '-vcodec', 'libx264',  # Video codec
        '-vf', "pad=ceil(iw/2)*2:ceil(ih/2)*2",
        '-y',
        '-r', '30',  # Frame rate
        video_name
    ]

    subprocess.run(command)

def convert_images_to_video(files, output_video):
    videos = []
    durations = get_durations()
    for i, f in enumerate(files):
        j= i+1
        convert_image_to_video(f, f"slide_{i}.mp4", durations[i])
        videos.append(f"slide_{i}.mp4")
    combine_videos(videos, output_video)

def overlay(top, bottom):
    command = [
        'ffmpeg',
        '-y',
        '-i', bottom,
        '-i', top,
        '-filter_complex', '[1:v]scale=640:360[top]; [0:v][top]overlay',  # Video codec
        'overlayed.mp4',
    ]

    subprocess.run(command)

def clean_up():
    for file in os.listdir("."):
        if file.endswith(".png"):
            os.remove(file)
        if "slide_" in file and file.endswith(".mp4"):
            os.remove(file)
    os.remove("slide_videos.txt")

# Example usage
files = pdf_to_png("test.pdf")
convert_images_to_video(files, "output_video.mp4")
loop_video(10, "normal_short.mp4", "normal.mp4")
overlay("normal.mp4", "output_video.mp4")
clean_up()