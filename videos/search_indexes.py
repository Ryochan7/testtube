from haystack import indexes

from .models import Media

class MediaIndex(indexes.ModelSearchIndex, indexes.Indexable):
  media_id = indexes.IntegerField(model_attr="id")
  #text = indexes.CharField(document=True, use_template=True)
  #title = indexes.CharField(model_attr="title")
  #description = indexes.CharField(model_attr="description")
  class Meta(object):
    model = Media
    fields = ["title", "description"]

  def index_queryset(self, using=None):
    return Media.public_objects.all()

  def read_queryset(self, using=None):
    return Media.objects.all().select_related()

  def get_updated_field(self):
    return "updated_date"

