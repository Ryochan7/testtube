import os
import subprocess
import json

def get_ffprobe_info(filepath):
  command = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", filepath]
  ffprobe_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, universal_newlines=True)
  stdout, stderr = ffprobe_process.communicate()
  jsonout = json.loads(stdout)
  return jsonout

#def should_convert(filepath):
def should_convert(ffprobe_json):
  result = True
  h264stream = False;
  aacstream = False;
  mp4File = False;
  large_resolution = False
  frame_rate_raw = 30

  fileExt = os.path.splitext(ffprobe_json["format"]["filename"])[1]
  if fileExt == ".mp4":
    file_streams = ffprobe_json["streams"]
    file_format = ffprobe_json["format"]["format_long_name"]
    mp4File = file_format == "QuickTime / MOV"
    if mp4File:
      for stream in file_streams:
        codec = stream["codec_name"]
        if codec == "h264":
          h264stream = True
          frame_rate_raw = eval(stream["avg_frame_rate"])
          if stream["width"] > 1920 or stream["height"] > 1080:
            large_resolution = True

        elif codec == "aac":
          aacstream = True

        if h264stream and aacstream:
          break

    bitrate = int(ffprobe_json["format"]["bit_rate"])
  else:
    mp4File = False

  if mp4File and bitrate <= 1572864 and (h264stream and aacstream) and not large_resolution and (10 <= frame_rate_raw <= 30):
  #if mp4File and bitrate <= 3145728 and (h264stream and aacstream):
    result = False

  print("FINAL RESULT: {}".format(result))
  return result

def get_duration(ffprobe_json):
  tmp_duration = ffprobe_json["format"]["duration"]
  duration = int(float(tmp_duration)) if tmp_duration else 0
  return duration

def get_frame_rate(ffprobe_json):
  result = 30
  frame_rate_raw = ""
  for stream in ffprobe_json["streams"]:
    if stream["codec_type"] == "video":
      frame_rate_raw = stream["avg_frame_rate"]

    if frame_rate_raw:
      result = eval(frame_rate_raw)
      break

  return result



def get_display_resolution(ffprobe_json):
  result = {"width": 0, "height": 0}
  for stream in ffprobe_json["streams"]:
    if stream["codec_type"] == "video":
      result["width"] = int(stream["width"])
      result["height"] = int(stream["height"])
      break

  return result

