from django.apps import AppConfig


class VideosConfig(AppConfig):
  name = 'videos'

  def ready(self):
    import videos.signals

