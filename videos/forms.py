import os

from django.conf import settings
from django import forms
from django.urls import reverse
from django.core.validators import FileExtensionValidator

from resumable.fields import ResumableFileField
from resumable.widgets import ResumableFileInput

from haystack.forms import SearchForm

from .models import Media, MediaCategory


class TestMediaUploadForm(forms.ModelForm):
  
  media_file = ResumableFileField(
    chunks_dir=getattr(settings, "FILE_CHUNKS_UPLOAD_DIR"),
  )

  def __init__(self, *args, **kwargs):
    requser = kwargs.pop("user", None)
    super().__init__(*args, **kwargs)
    self.fields["media_file"].upload_url = reverse("videos:uploadchunk")
    if requser:
      base_chunks_dir = getattr(settings, "FILE_CHUNKS_UPLOAD_DIR")
      self.fields["media_file"].chunks_dir = os.path.join(base_chunks_dir, requser.username)
    else:
      raise Exception("No user instance passed to form")

    cats = MediaCategory.objects.all()
    choices = []
    for cat in cats:
      choices.append((cat.id, cat.title))

    self.fields["category"] = forms.ChoiceField(choices=choices, initial=1)

  def clean_category(self):
    data = self.cleaned_data["category"]
    category = MediaCategory.objects.filter(id=data).first()
    if not category:
      raise forms.ValidationError("MediaCategory with id={} does not exist".format(data))

    return category

  class Meta(object):
    model = Media
    fields = ["media_file", "title", "category", "rating", "description", "thumbnail", "tags"]


class SearchMediaForm(SearchForm):
  pass


class VideoOptions (forms.Form):
  autoplay = forms.BooleanField(initial=False)

