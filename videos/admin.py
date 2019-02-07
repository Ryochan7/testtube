from django.contrib import admin
from django import forms
from django.forms import ModelForm
from django.forms.widgets import ClearableFileInput
from sorl.thumbnail.admin import AdminImageMixin
from sorl.thumbnail import ImageField

from django.db import models

from .models import (Media, MediaCategory, MediaPlaylist, MediaSubscription,
MediaFeaturedItem, MediaReaction)

class MediaThumbInput(ClearableFileInput):
  template_name = "videos/forms/widgets/clearable_file_input.html"

class MediaAdminForm(ModelForm):
  class Meta(object):
    model = Media
    fields = "__all__"
    widgets = {
      "thumbnail": MediaThumbInput
    }

  def clean_tags(self):
    print(self.cleaned_data["tags"])
    temp_tags = self.cleaned_data["tags"]
    #print(type(temp_tags[0]))
    if len(temp_tags) > 3:
      raise forms.ValidationError("Only three tags allowed")

    for tag in temp_tags:
      if "," in tag:
        raise forms.ValidationError("Tags string cannot contain commas")
      elif len(tag) > 20:
        raise forms.ValidationError("No tag can be longer than 20 chars")

    return temp_tags


class MediaAdmin(admin.ModelAdmin):
  form = MediaAdminForm
  list_display = ("title", "creation_date", "status", "visibility",)
  list_filter = ("status",)
  prepopulated_fields = {"slug": ("title",)}
  exclude = ("view_count","uuid_code", "creation_date", "updated_date", "duration",)
  search_fields = ("title",)
  #formfield_overrides = {
  #  models.CharField: {"widget": Textarea}
  #}


class MediaCategoryAdmin(admin.ModelAdmin):
  prepopulated_fields = {"slug": ("title",)}


class MediaPlaylistAdmin(admin.ModelAdmin):
  prepopulated_fields = {"slug": ("name",)}
  autocomplete_fields = ["media"]


class MediaFeaturedItemAdmin(admin.ModelAdmin):
  list_select_related = ("media",)
  autocomplete_fields = ["media"]


class MediaReactionAdmin(admin.ModelAdmin):
  list_select_related = ("sender",)
  autocomplete_fields = ("sender", "media",)


# Register your models here.
admin.site.register(Media, MediaAdmin)
admin.site.register(MediaCategory, MediaCategoryAdmin)
admin.site.register(MediaPlaylist, MediaPlaylistAdmin)
admin.site.register(MediaSubscription)
admin.site.register(MediaFeaturedItem, MediaFeaturedItemAdmin)
admin.site.register(MediaReaction, MediaReactionAdmin)

#admin.site.register(Media)
#admin.site.register(MediaCategory)
