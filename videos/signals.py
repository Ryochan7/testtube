import os
import uuid

from django.db.models import signals
from django.dispatch import receiver
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.transaction import on_commit
from django.db.models import F, Q, OuterRef, Subquery

from testtube_custom.models import SiteUser

from .tasks import encode_video_file
from .utils import should_convert, get_ffprobe_info, get_duration

from .models import Media, MediaView, MediaSubscription

@receiver(signals.post_save, sender=Media)
def check_for_video_processing(sender, **kwargs):
  #print("IN METHOD")
  instance = kwargs["instance"]
  if (kwargs["created"] and not kwargs["raw"] and 
    instance.status == Media.PENDING):
    fs = FileSystemStorage(location=settings.TMP_UPLOAD_ROOT)
    outfile_path = fs.path(instance.media_file.name)
    print(instance.media_file.name)
    print(outfile_path)
    #encode_video_file.s(instance.id).apply_async(countdown=20)
    ffprobe_json = get_ffprobe_info(outfile_path)
    if should_convert(ffprobe_json):
      on_commit(lambda: encode_video_file.delay(instance.id))
    else:
      instance.mark_ready()
      instance.duration = get_duration(ffprobe_json)
      media_file_name = instance.media_file.name
      basedir = os.path.dirname(media_file_name)
      output_filename = "{}.mp4".format(instance.uuid_code)
      output_media_name = os.path.join(basedir, output_filename)
      output_file_path = os.path.join(settings.MEDIA_ROOT, output_media_name)
      os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
      os.rename(outfile_path, output_file_path)
      instance.media_file.name = output_media_name
      instance.save(update_fields=["status", "visibility", "duration", "media_file", "publish_date"])
      instance.uploader.video_count = F("video_count") + 1
      instance.uploader.save(update_fields=["video_count"])

@receiver(signals.post_save, sender=Media)
def increment_num_sub_notifications(sender, **kwargs):
  instance = kwargs["instance"]
  if kwargs["created"] and not kwargs["raw"]:
    SiteUser.objects.filter(subscriber__subbed_id=instance.uploader_id).update(unseen_sub_upload_count = F("unseen_sub_upload_count") + 1)

@receiver(signals.post_save, sender=MediaView)
def increment_channel_view_count(sender, **kwargs):
  instance = kwargs["instance"]
  if kwargs["created"] and not kwargs["raw"]:
    SiteUser.objects.filter(id=instance.media.uploader_id).update(view_count = F("view_count") + 1)

@receiver(signals.post_save, sender=MediaSubscription)
def increment_channel_sub_count(sender, **kwargs):
  instance = kwargs["instance"]
  if kwargs["created"] and not kwargs["raw"]:
    SiteUser.objects.filter(id=instance.subbed_id).update(sub_count = F("sub_count") + 1)

@receiver(signals.post_delete, sender=MediaSubscription)
def decrement_channel_sub_count(sender, **kwargs):
  instance = kwargs["instance"]
  SiteUser.objects.filter(id=instance.subbed_id).update(sub_count = F("sub_count") - 1)

