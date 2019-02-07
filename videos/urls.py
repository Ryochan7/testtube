from django.urls import path
from django.contrib.auth.decorators import login_required

from . import views

app_name = "videos"
urlpatterns = [
  path("", views.MediaIndex.as_view(), name="medialist"),
  path("recent", views.MediaListIndex.as_view(), name="recentlist"),
  path("featured", views.MediaFeaturedList.as_view(), name="featured"),
  path("upload", views.UploadFormView.as_view(), name="upload"),
  path("submit-upload", views.UploadView.as_view(), name="submitupload"),
  path('upload-chunk', login_required(views.TestResumableView.as_view()), name='uploadchunk'),
  path("play/<uuid:uuid_code>", views.WatchView.as_view(), name="watch"),
  path("category/<slug:slug>", views.CategoryView.as_view(), name="category"),
  path("tag/<slug:slug>", views.MediaTaggedList.as_view(), name="tagged"),
  path("top-uploads", views.TopMediaList.as_view(), name="topmedia"),
  path("popular/<str:period>", views.PopularMediaList.as_view(), name="popular"),
  path("feed/history", login_required(views.MediaHistoryList.as_view()), name="playhistory"),
  path("playlist/<slug:slug>", login_required(views.MediaPlaylistView.as_view()), name="playlist"),
  path("subscriptions", login_required(views.MediaSubscriptionChannelView.as_view()), name="subscriptions"),
  path("subscriptions/latest", login_required(views.MediaSubscriptionMediaView.as_view()), name="subscribemedia"),
  path("channel/<slug:slug>", views.ChannelView.as_view(), name="channel"),
  path("search/", views.MediaSearchView.as_view(), name="search"),
  path("reaction/<int:id>", views.MediaReactionChange.as_view(), name="changereaction"),
  path("toggle-subscription/<int:id>", views.ToggleSubscription.as_view(), name="togglesub"),
]

