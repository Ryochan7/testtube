import os

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.conf import settings
from django.template.defaultfilters import slugify
from django.urls import reverse

def validate_profile_image_ext(value):
  allowed_mimes = ["image/png", "image/jpeg"]
  allowed_extensions_list = ["png", "jpg", "jpeg"]
  #file_ext = os.path.splitext(value)[1]
  #mime = magic.Magic(mime=True)
  #print(value.name)
  #print(value.path)
  #mimetype = mime.from_file(os.path.join(value.storage.location, value.name))
  #mimetype = mime.from_file(value)
  #mimetype = value.content_type
  #if mimetype not in allowed_mimes:
  #  raise ValidationError("Uploaded image is not an allowed file type")
  validator = FileExtensionValidator(allowed_extensions=allowed_extensions_list)
  validator(value)

def profile_image_uploadto(instance, filename):
  username = instance.username
  print(instance.username)
  print(dir(instance))
  firstletter = username[0]
  file_ext = os.path.splitext(filename)[1]
  return "profile_pics/{}/{}.{}".format(firstletter, username, file_ext)

# Create your models here.
class SiteUser(AbstractUser):
  profile_image = models.ImageField(upload_to=profile_image_uploadto, max_length=200, default="5ad160d61e8ba.jpeg", validators=[validate_profile_image_ext])
  slug = models.SlugField()
  view_count = models.IntegerField(default=0)
  sub_count = models.IntegerField(default=0)
  unseen_sub_upload_count = models.PositiveIntegerField(default=0)
  video_count = models.PositiveIntegerField(default=0)

  def save(self, *args, **kwargs):
    if not self.slug:
      self.slug = slugify(self.username)[:50]

    super().save(*args, **kwargs)

  def get_absolute_url(self):
    return reverse("videos:channel", args=(self.slug,))

  def calculate_stats(self):
    from videos import models as media_models
    self.view_count = media_models.MediaView.objects.filter(media__uploader=self).count()
    self.sub_count = media_models.MediaSubscription.objects.filter(subbed=self).count()
    self.video_count = media_models.Media.public_objects.filter(uploader_id=self.id).count()

  def has_unseen_sub_vids(self):
    return self.unseen_sub_upload_count > 0

