from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.

class Reaction(models.Model):
  LIKE = 0
  DISLIKE = 1

  REACT_CHOICES = (
    (LIKE, "Like"),
    (DISLIKE, "Dislike"),
  )

  sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  reaction = models.IntegerField(choices=REACT_CHOICES)
  date = models.DateTimeField(auto_now=True)

  content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
  object_id = models.PositiveIntegerField()
  content_object = GenericForeignKey()

  def __str__(self):
    return str(self.id)

