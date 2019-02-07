import subprocess
import os
import uuid
import math

from testtube.celery import app
#from testtube.utils import randomword

from django.db.models import F
from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import UploadedFile
from django.utils.crypto import get_random_string
from django.utils import timezone

from .models import Media
from .utils import (get_ffprobe_info, get_duration, get_frame_rate,
get_display_resolution)

@app.task
def encode_video_file(media_id):
  print("IN `encode_video_file` THIS TASK")
  print("USING {}".format(media_id))
  instance = Media.objects.filter(id=media_id).first()
  if not instance:
    print("INSTANCE NOT FOUND")
    return

  print("Processing: {} ({})".format(instance.title, media_id))

  filepath = os.path.join(settings.TMP_UPLOAD_ROOT, instance.media_file.name)
  ffprobe_json = get_ffprobe_info(filepath)
  media_file_name = instance.media_file.name
  basefile = os.path.basename(media_file_name)
  basedir = os.path.dirname(media_file_name)
  print("FILEPATH: {}".format(media_file_name))
  print("BASEFILE: {}".format(basefile))
  dirname = os.path.dirname(filepath)
  basename = os.path.splitext(basefile)[0]

  output_filename = "{}.mp4".format(instance.uuid_code)
  output_media_name = os.path.join(basedir, output_filename)
  output_dirpath = os.path.join(settings.MEDIA_ROOT, basedir)
  output_filepath = os.path.join(output_dirpath, output_filename)
  #output_filename = "{}.mp4".format(basename)
  #output_filename = "{}.mp4".format(get_random_string(10))
  tmp_encode_filepath = "{}_temp.mp4".format(os.path.join(dirname, basename))

  instance.status = Media.PROCESSING
  Media.objects.filter(id=media_id).update(status=Media.PROCESSING, updated_date=timezone.now())
  instance.media_file.close()
  framerate = min(30, max(10, get_frame_rate(ffprobe_json)))
  gop = math.ceil(framerate) * 2
  cpulimit = "40"
  resolution_data = get_display_resolution(ffprobe_json)
  large_resolution = resolution_data["width"] > 1920 and resolution_data["height"] > 1080
  weird_resolution = not large_resolution and (resolution_data["width"] > 1920 or resolution_data["height"] > 1080)
  command = ["nice", "-n", "10", "ffmpeg", "-i", filepath, "-c:v", "libx264", "-preset", "medium", "-profile:v", "high", "-level", "4.0", "-crf", "30", "-maxrate", "1500k", "-bufsize", "2M", "-movflags", "+faststart", "-g", str(gop), "-r", str(framerate)]

  # Only resize video if width or height exceed 1080p spec
  if large_resolution:
    command.extend(["-vf", "scale=1920:-2"])
  elif weird_resolution:
    command.extend(["-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2"])

  command.extend(["-c:a", "aac", "-b:a", "160k", "-strict", "-2", "-threads", "0", "-y", tmp_encode_filepath])
  
  print("START ENCODE")
  print(command)
  print(" ".join(command))
  ffmpeg_task = subprocess.Popen(command, stdin = subprocess.PIPE)
  if settings.RUN_CPULIMIT_FFMPEG:
    cpulim_command = ["cpulimit", "-p", str(ffmpeg_task.pid), "-l", cpulimit, "-b"]
    print("FFMPEG PID: {}".format(ffmpeg_task.pid))
    cpulimit_proc = subprocess.Popen(cpulim_command)

  ffmpeg_task.wait()
  os.makedirs(output_dirpath, exist_ok=True)
  os.rename(tmp_encode_filepath, output_filepath)

  print("FILEPATH: {}".format(media_file_name))
  print("BASEFILE: {}".format(basefile))
  fs2 = FileSystemStorage(location=settings.TMP_UPLOAD_ROOT)
  fs2.delete(media_file_name)
  instance = Media.objects.filter(id=media_id).first()
  if instance:
    instance.mark_ready()
    instance.duration =  get_duration(ffprobe_json)
    instance.media_file.name = output_media_name
    instance.save(update_fields=["status", "visibility", "media_file", "duration", "publish_date", "updated_date"])
    instance.uploader.video_count = F("video_count") + 1
    instance.uploader.save(update_fields=["video_count"])
    print("Saved: {} ({})".format(instance.title, media_id))

  print("EXIT `encode_video_file` TASK")
