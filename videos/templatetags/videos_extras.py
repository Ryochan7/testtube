from django import template
from django.conf import settings
from django.db.models.expressions import RawSQL

from videos.models import Media, MediaFeaturedItem

register = template.Library()

@register.inclusion_tag("videos/partials/latest.html", takes_context=True)
def latest_media(context):
  data = {"media_objects": Media.public_objects.all().order_by("-id")[:20]}
  return data

@register.simple_tag
def get_related_videos(current_media):
  related_content = Media.public_objects.filter(category=current_media.category.id).exclude(id=current_media.id).select_related("uploader").order_by("-id")[:10]
  return related_content

@register.simple_tag
def get_playlist_videos(current_media, playlist_id):
  #inner_id = Media.objects.filter(id=current_media.id, mediaplaylist__id=playlist_id).annotate(inner_id=RawSQL("videos_mediaplaylist_media.id", ())).values_list("inner_id", flat=True).first()
  related_content = Media.public_objects.filter(mediaplaylist__id=playlist_id).extra(where=["videos_mediaplaylist_media.id < %s"], params=[current_media.inner_playlist_id]).select_related("uploader").order_by("-videos_mediaplaylist_media.id")[:10]
  return related_content

@register.simple_tag
def get_recent_videos():
  return Media.objects.filter(visibility=Media.PUBLIC).select_related().defer("media_file")[:20]

@register.simple_tag
def get_featured_videos():
  return MediaFeaturedItem.objects.all().select_related()[:20]

