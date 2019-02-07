import datetime
import uuid
import os
import re

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.safestring import mark_safe
from sorl.thumbnail import ImageField
from taggit.managers import TaggableManager
#from reacts.models import Reaction

from .storage import FileMoveSystemStorage

re_timestamptext = re.compile(r"(\d{2}:)?(\d{1,2})?:(\d{2})")

# Create your models here.

def thumbnail_user_upload_to(instance, filename):
  current_date = datetime.datetime.now()
  uuid_code = instance.uuid_code.hex
  username = instance.uploader.username.lower()
  file_ext = os.path.splitext(filename)[1]
  return "media_uploads/{}/{}/{}/thumbs/{}{}".format(username, current_date.year, current_date.strftime("%m"), uuid_code, file_ext)

def tmp_media_upload_to(instance, filename):
  current_date = datetime.datetime.now()
  uuid_code = instance.uuid_code.hex
  username = instance.uploader.username.lower()
  file_ext = os.path.splitext(filename)[1]
  return "media_uploads/{}/{}/{}/{}{}".format(username, current_date.year, current_date.strftime("%m"), uuid_code, file_ext)

def default_media_cat():
  return MediaCategory.objects.only("id").get_or_create(id=1, slug="other", defaults={"title": "Other"})[0].id


class MediaCategory(models.Model):
  title = models.CharField(max_length=50, unique=True)
  slug = models.SlugField()
  summary = models.CharField(max_length=200, blank=True)
  description = models.TextField(blank=True)

  def __str__(self):
    return self.title

  class Meta(object):
    verbose_name_plural = "Media Categories"

  def get_absolute_url(self):
    return reverse("videos:category", args=(self.slug,))


class PublishedMediaManager(models.Manager):
  def get_queryset(self):
    return super().get_queryset().filter(status=Media.PUBLISHED,
visibility=Media.PUBLIC)


class Media(models.Model):
  PENDING = 0
  PROCESSING = 1
  PUBLISHED = 2
  ERROR = 3

  MEDIA_STATE = (
    (PENDING, "Pending"),
    (PROCESSING, "Processing"),
    (PUBLISHED, "Published"),
    (ERROR, "Error"),
  )

  UNPUBLISHED = 0
  PUBLIC = 1
  UNLISTED = 2
  PRIVATE = 3

  PUBLISHED_STATUS = (
    (UNPUBLISHED, "Unpublished"),
    (PUBLIC, "Public"),
    (UNLISTED, "Unlisted"),
    (PRIVATE, "Private"),
  )

  ALL_AGES = 0
  NSFW = 1
  NSFL = 2
  RATING_CHOICES = (
    (ALL_AGES, "All Ages"),
    (NSFW, "NSFW"),
    (NSFL, "NSFL"),
  )

  title = models.CharField(max_length=100)
  slug = models.SlugField()
  uuid_code = models.UUIDField(default=uuid.uuid4, editable=False, db_index=True)
  media_file = models.FileField(upload_to=tmp_media_upload_to, max_length=200, storage=FileMoveSystemStorage(location=settings.TMP_UPLOAD_ROOT))
  description = models.TextField(blank=True)
  uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING, default=None)
  view_count = models.IntegerField(default=0, db_index=True)
  creation_date = models.DateTimeField(default=timezone.now)
  updated_date = models.DateTimeField(default=timezone.now)
  category = models.ForeignKey(MediaCategory, on_delete=models.CASCADE,
default=default_media_cat)
  thumbnail = ImageField(upload_to=thumbnail_user_upload_to, max_length=200)
  status = models.IntegerField(default=0, choices=MEDIA_STATE)
  visibility = models.IntegerField(default=0, choices=PUBLISHED_STATUS)
  rating = models.IntegerField(default=ALL_AGES, choices=RATING_CHOICES)
  publish_date = models.DateTimeField(default=timezone.now)
  # Rename to duration
  duration = models.IntegerField(default=0)
  #file_size = models.PositiveIntegerField(default=0)
  #reacts = GenericRelation(Reaction, related_query_name="reactions")

  objects = models.Manager() # The default manager
  public_objects = PublishedMediaManager()
  tags = TaggableManager(blank=True, help_text="Up to three space-separated list of tags")

  def __str__(self):
    return self.title

  class Meta(object):
    verbose_name = "Media File"
    verbose_name_plural = "Media Files"
    ordering = ["-id"]
    #indexes = [
    #  models.Index(fields=['status', 'visibility'], name="Main Listing"),
    #]

  def save(self, *args, **kwargs):
    if not self.slug:
      self.slug = slugify(self.title)[:50]

    self.updated_date = timezone.now()
    super().save(*args, **kwargs)

  def get_absolute_url(self):
    return reverse("videos:watch", args=(self.uuid_code,))

  def get_admin_url(self):
    return reverse("admin:{}_{}_change".format(self._meta.app_label, self._meta.model_name), args=(self.id,))

  @property
  def is_public(self):
    return (self.status == self.__class__.PUBLISHED and
self.visibility == self.__class__.PUBLIC)

  @property
  def public_view_count(self):
    current = self.view_count
    if self.view_count > 300 and self.creation_date + datetime.timedelta(hours=12) < timezone.now():
      current = 300

    return current

  def mark_ready(self):
    self.status = self.__class__.PUBLISHED
    self.visibility = self.__class__.PUBLIC
    self.publish_date = timezone.now()

  def media_file_ext(self):
    return os.path.splitext(self.media_file.name)[1]

  def media_format_duration(self):
    seconds = int(self.duration % 60)
    minutes = int(self.duration / 60 % 60)
    hours = int(self.duration / 3600)
    format_str = ""
    if hours > 0:
      format_str = "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)
    else:
      format_str = "{:02d}:{:02d}".format(minutes, seconds)
    return format_str

  def sorted_tags(self):
    return self.tags.all().order_by("name")

  def output_description(self):
    def inner_repl(match):
      hour = match.group(1)
      minute = match.group(2)
      second = match.group(3)
      duration = int(hour.strip(":")) * 3600 if hour else 0
      duration = duration + ((int(minute.strip(":")) * 60) if minute else 0)
      duration = duration + int(second.strip(":"))
      final = "<a href=\"{}?t={}\" data-seektime=\"{}\">{}</a>".format(self.get_absolute_url(), duration, duration, match.group(0))
      return final

    temp = re_timestamptext.sub(inner_repl, self.description).strip()
    return mark_safe(temp)


class MediaView(models.Model):
  visitor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
  logged_ip = models.GenericIPAddressField()
  media = models.ForeignKey(Media, on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now=True, db_index=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta(object):
    verbose_name = "Media View"
    verbose_name_plural = "Media Views"
    """indexes = [
      models.Index(fields=['media', 'logged_ip', 'id'], name="Check Anon Media View"),
      models.Index(fields=['media', 'visitor', 'id'], name="Check Visitor Media View"),
    ]
    """


class MediaHistoryItem(models.Model):
  visitor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  media = models.ForeignKey(Media, on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now=True)
  updated_at = models.DateTimeField(auto_now=True, db_index=True)

  class Meta(object):
    verbose_name = "Media History Item"
    verbose_name_plural = "Media History Items"


class MediaPlaylist(models.Model):
  PUBLIC = 0
  PRIVATE = 1

  PRIVACY_STATE = (
    (PUBLIC, "Public"),
    (PRIVATE, "Private"),
  )

  owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  name = models.CharField(max_length=100)
  slug = models.SlugField()
  description = models.TextField(blank=True)
  media = models.ManyToManyField(Media)
  privacy = models.IntegerField(default=PUBLIC, choices=PRIVACY_STATE)
  created_at = models.DateTimeField(auto_now=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta(object):
    verbose_name = "Media Playlist"
    verbose_name_plural = "Media Playlists"

  def __str__(self):
    return self.name

  def save(self, *args, **kwargs):
    if not self.slug:
      self.slug = slugify(self.title)[:50]

    self.updated_at = timezone.now()
    super().save(*args, **kwargs)

  def get_absolute_url(self):
    return reverse("videos:playlist", args=(self.slug,))


class MediaSubscription(models.Model):
  subscriber = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriber")
  subbed = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subbed")
  origin_media = models.ForeignKey(Media, on_delete=models.CASCADE, null=True)
  created_at = models.DateTimeField(auto_now=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta(object):
    verbose_name = "Media Subscription"
    verbose_name_plural = "Media Subscriptions"

  def __str__(self):
    return "[{}] subbed to [{}]".format(self.subscriber, self.subbed)


class MediaFeaturedItem(models.Model):
  media = models.ForeignKey(Media, on_delete=models.CASCADE)

  class Meta(object):
    verbose_name = "Featured Media"
    verbose_name_plural = "Featured Media Items"
    ordering = ["-id"]

  def __str__(self):
    return self.media.title


class MediaReaction(models.Model):
  LIKE = 0
  DISLIKE = 1

  REACT_CHOICES = (
    (LIKE, "Like"),
    (DISLIKE, "Dislike"),
  )

  sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  media = models.ForeignKey(Media, on_delete=models.CASCADE)
  reaction = models.IntegerField(choices=REACT_CHOICES, db_index=True)
  date = models.DateTimeField(auto_now=True)

  def __str__(self):
    return str(self.id)

  class Meta(object):
    verbose_name = "Reaction"
    verbose_name_plural = "Reactions"
    unique_together = ("sender", "media", "reaction")

