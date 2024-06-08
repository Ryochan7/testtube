import os
import datetime
from dateutil.relativedelta import relativedelta

from django.http import (HttpResponse, Http404, JsonResponse,
HttpResponseBadRequest)
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views.generic.base import TemplateView
from django.views.generic import DetailView, ListView
from django.views import View
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db.models import F, Q, OuterRef, Subquery
from django.db.models.expressions import RawSQL
#from django.db.transaction import on_commit
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.db.models import Count, Max
from django.db.models import OuterRef, Subquery

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from django.utils.decorators import method_decorator
from django.core.paginator import InvalidPage, Paginator

from resumable.views import ResumableUploadView
from taggit.models import Tag
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet

from testtube.utils import randomword, get_client_ip

from testtube_custom.models import SiteUser

from .tasks import encode_video_file
from .forms import TestMediaUploadForm, SearchMediaForm, VideoOptions
from .utils import should_convert
from .models import (Media, MediaView, MediaCategory, MediaHistoryItem,
MediaPlaylist, MediaSubscription, MediaFeaturedItem, MediaReaction)

# Create your views here.

class UploadFormView(TemplateView):
  template_name = "videos/upload.html"

  @method_decorator(login_required)
  def dispatch(self, *args, **kwargs):
    return super().dispatch(*args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super(UploadFormView, self).get_context_data(**kwargs)
    context["form"] = TestMediaUploadForm(user=self.request.user)
    return context


class UploadView(View):
  @method_decorator(login_required)
  def dispatch(self, *args, **kwargs):
    return super().dispatch(*args, **kwargs)

  def post(self, request):
    data = request.POST.copy()
    form = TestMediaUploadForm(data, request.FILES, user=request.user)
    if form.is_valid():
      new_media = form.save(commit=False)
      new_media.uploader = request.user
      new_media.save()
      form.save_m2m()
      #on_commit(lambda: encode_video_file.delay(new_media.id))

      return redirect("videos:medialist")
    

class WatchView(DetailView):
  queryset = Media.objects.all().select_related()
  template_name = "videos/watch.html"

  def get(self, request, *args, **kwargs):
    self.object = self.get_object()

    user = request.user
    ip_addr = get_client_ip(request)
    media_view = None
    self.user_is_authenticated = user.is_authenticated
    if self.user_is_authenticated:
      media_view = MediaView.objects.filter(Q(visitor=user) |
Q(logged_ip=ip_addr), media=self.object).order_by("-id").first()

      in_history = MediaHistoryItem.objects.filter(visitor=user, media=self.object).exists()
      if in_history:
        MediaHistoryItem.objects.filter(media=self.object).update(updated_at=timezone.now())
      else:
        MediaHistoryItem.objects.create(visitor=user, media=self.object)

    else:
      user = None
      media_view = MediaView.objects.filter(logged_ip=ip_addr,
media=self.object).order_by("-id").first()

    if not media_view or (media_view.created_at + datetime.timedelta(days=1) < timezone.now()):
      media_view = MediaView.objects.create(visitor=user, logged_ip=ip_addr, media=self.object)
      old_view_count = self.object.view_count
      self.object.view_count = F("view_count") + 1
      self.object.save(update_fields=["view_count"])
      self.object.view_count = old_view_count + 1
      #self.object.refresh_from_db()

    context = self.get_context_data(object=self.object)
    return self.render_to_response(context)

  def get_object(self, queryset=None):
    return get_object_or_404(self.get_queryset(), uuid_code=self.kwargs.get("uuid_code"))

  def get_context_data(self, **kwargs):
    is_subbed = False
    if self.user_is_authenticated:
      sub = MediaSubscription.objects.filter(subscriber=self.request.user, subbed=self.object.uploader).exists()
      is_subbed = sub

    num_likes = self.object.mediareaction_set.filter(reaction=MediaReaction.LIKE).count()
    num_dislikes = self.object.mediareaction_set.filter(reaction=MediaReaction.DISLIKE).count()
    total_reactions = num_likes + num_dislikes

    playlist_id = self.request.GET.get("list", None)
    playlist_id = int(playlist_id) if playlist_id and playlist_id.isnumeric() else None
    next_video = None
    related_cache = []
    if not playlist_id:
      next_video = Media.public_objects.filter(id__lt=self.object.id, category=self.object.category).select_related("uploader").first()
    else:
      inner_id = Media.objects.filter(id=self.object.id, mediaplaylist__id=playlist_id).annotate(inner_id=RawSQL("videos_mediaplaylist_media.id", ())).values_list("inner_id", flat=True).first()
      if inner_id:
        related_cache = list(Media.public_objects.filter(mediaplaylist__id=playlist_id).extra(where=["videos_mediaplaylist_media.id < %s"], params=[inner_id]).select_related("uploader").order_by("-videos_mediaplaylist_media.id")[:10])
        next_video = next(iter(related_cache[:1]), None)
        if not next_video:
          playlist_id = None

    form = None
    if self.request.COOKIES.get("autoplay", None):
      form = VideoOptions(self.request.COOKIES)
      # If form is not valid, reset form
      if not form.is_valid():
        form = VideoOptions()
    else:
      form = VideoOptions()

    if self.request.user.is_authenticated:
      current_react = self.object.mediareaction_set.filter(sender=self.request.user).first()
    else:
      current_react = None

    start_time = self.request.GET.get("t", "")
    start_time = int(start_time) if start_time.isnumeric() else None
    context = super().get_context_data(**kwargs)
    extra_data = {
      "likes": num_likes,
      "dislikes": num_dislikes,
      "like_percent": int((num_likes / total_reactions) * 100.0) if total_reactions > 0 else 0,
      "current_react": current_react,
      "is_subbed": is_subbed,
      "autoplay_form": form,
      "next_video": next_video,
      "list": playlist_id,
      "related_media": related_cache,
      "start_time": start_time
    }

    context.update(extra_data)
    return context


class MediaIndex(TemplateView):
  template_name = "videos/index.html"


class MediaListIndex(ListView):
  queryset = Media.objects.filter(visibility=Media.PUBLIC).select_related().defer("media_file").order_by("-id")
  paginate_by = 20
  template_name = "videos/recent.html"


class MediaFeaturedList(ListView):
  queryset = MediaFeaturedItem.objects.all().select_related()
  paginate_by = 20
  template_name = "videos/featured.html"


class MediaTaggedList(ListView):
  queryset = Media.public_objects.select_related().defer("media_file")
  paginate_by = 20
  template_name = "videos/tagged.html"
  ordering = "-id"
  context_name = "media"

  def get_queryset(self):
    applicable_tag = self.kwargs.get("slug")
    if applicable_tag:
      return super().get_queryset().filter(tags__slug=applicable_tag)

    return super().get_queryset().none()

  def get_context_data(self, **kwargs):
    tag = get_object_or_404(Tag, slug=self.kwargs.get("slug"))
    context = super().get_context_data(**kwargs)
    context["tag"] = tag
    return context



class TestResumableView(ResumableUploadView):
  @property
  def chunks_dir(self):
    return os.path.join(settings.FILE_CHUNKS_UPLOAD_DIR, self.request.user.username)


class CategoryView(ListView):
  paginate_by = 20
  template_name = "videos/category.html"

  def get_queryset(self):
    return Media.public_objects.filter(category__slug=self.kwargs.get("slug")).select_related().defer("media_file").order_by("-id")

  def get_context_data(self, **kwargs):
    cat = get_object_or_404(MediaCategory, slug=self.kwargs.get("slug"))
    context = super().get_context_data(**kwargs)
    context["category"] = cat
    context["is_cat"] = True
    return context


class TopMediaList(ListView):
  queryset = Media.public_objects.all().select_related().defer("media_file").order_by("-view_count")
  paginate_by = 20
  template_name = "videos/top-videos.html"


class PopularMediaList(ListView):
  paginate_by = 20
  template_name = "videos/popular.html"

  def get_queryset(self):
    period = self.kwargs.get("period", "")
    if period not in ["day", "week", "month"]:
      raise Http404("Invalid period specified")

    current = timezone.now()
    begin_date = current
    #media_view.created_at + datetime.timedelta(days=1) < timezone.now()
    if period == "day":
      begin_date = current - datetime.timedelta(days=1)
    elif period == "week":
      begin_date = current - datetime.timedelta(days=7)
    elif period == "month":
      begin_date = current - relativedelta(months=1)

    real_media = Media.public_objects.filter(mediaview__created_at__gt=begin_date).annotate(date_views=Count("mediaview__id")).defer("media_file").select_related().order_by("-date_views")
    return real_media

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context["in_pop"] = True
    return context


class MediaHistoryList(ListView):
  queryset = Media.objects.all()
  paginate_by = 20
  #ordering = "-access_id"
  #ordering = "-id"
  ordering = "-mediahistoryitem__updated_at"
  template_name = "videos/history.html"

  def get_queryset(self):
    media_query = super().get_queryset().filter(mediahistoryitem__visitor=self.request.user).select_related()
    return media_query


class MediaPlaylistView(ListView):
  model = Media
  paginate_by = 20
  template_name = "videos/playlist.html"
  ordering = "-videos_mediaplaylist_media.id"

  def get_queryset(self):
    media_query = super().get_queryset().filter(mediaplaylist__slug=self.kwargs["slug"]).select_related()
    return media_query

  def get_context_data(self, **kwargs):
    playlist = get_object_or_404(MediaPlaylist, slug=self.kwargs.get("slug"))
    context = super().get_context_data(**kwargs)
    context["playlist"] = playlist
    return context


class MediaSubscriptionMediaView(ListView):
  model = Media
  paginate_by = 20
  template_name = "videos/sub_media.html"
  ordering = "-id"

  def get(self, request, *args, **kwargs):
    response = super().get(request, *args, **kwargs)
    if (request.user.is_authenticated and
request.user.unseen_sub_upload_count != 0):
      request.user.unseen_sub_upload_count = 0
      request.user.save(update_fields=["unseen_sub_upload_count"])

    return response
    

  def get_queryset(self):
    subs_query = MediaSubscription.objects.filter(subscriber=self.request.user).values_list("subbed", flat=True)
    return super().get_queryset().filter(uploader__in=subs_query).select_related()


class MediaSubscriptionChannelView(ListView):
  model = MediaSubscription
  paginate_by = 20
  template_name = "videos/sub_channel.html"
  ordering = "-id"

  def get_queryset(self):
    chan_query = super().get_queryset().filter(subscriber=self.request.user).select_related("subbed")
    return chan_query

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    return context


class ChannelView(DetailView):
  model = SiteUser
  template_name = "videos/channel.html"
  paginate_by = 20

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    media_query = self.object.media_set.all().select_related().order_by("-id")
    p = Paginator(media_query, self.paginate_by)
    try:
      page = p.page(self.request.GET.get("page", 1))
    except InvalidPage:
      page = None

    is_subbed = False
    if self.request.user.is_authenticated:
      sub = MediaSubscription.objects.filter(subscriber=self.request.user, subbed=self.object).exists()
      is_subbed = sub

    context["channel"] = self.object
    context["channel_media"] = page.object_list if page else Media.objects.none()
    context["channel_media_count"] = self.object.video_count #p.count
    #context["channel_sub_count"] = MediaSubscription.objects.filter(subbed=self.object).count()
    #context["channel_view_count"] = 0
    context["channel_sub_count"] = self.object.sub_count
    context["channel_view_count"] = self.object.view_count
    context["is_paginated"] = page.has_other_pages() if page else False
    context["page_obj"] = page
    context["paginator"] = p
    context["is_subbed"] = is_subbed
    #print(context)
    return context


class MediaSearchView(SearchView):
  queryset = SearchQuerySet().models(Media)
  paginate_by = 20
  form_class = SearchMediaForm

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    pag_page = context["page_obj"]
    if pag_page.has_next():
      get_query = self.request.GET.copy()
      get_query.update({"next_page": pag_page.next_page_number()})

    return context


class MediaReactionChange(LoginRequiredMixin, View):
  def post(self, request, *args, **kwargs):
    score = request.POST.get("react", -2)
    try:
      score = int(score)
    except:
      score = -2

    if score not in [-1, MediaReaction.LIKE, MediaReaction.DISLIKE]:
      return HttpResponseBadRequest()

    media = get_object_or_404(Media, id=kwargs["id"])
    reaction = MediaReaction.objects.filter(sender=request.user, media=media).first()

    if not reaction:
      reaction = MediaReaction.objects.create(sender=request.user, media=media, reaction=score)
    elif reaction and score == -1:
      reaction.delete()
    elif reaction:
      reaction.reaction = score
      reaction.save()
    else:
      return HttpResponseBadRequest()

    #if request.is_ajax():
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax:
      react_count = MediaReaction.objects.filter(media=media).count()
      likes = MediaReaction.objects.filter(media=media, reaction=MediaReaction.LIKE).count()
      like_percent = int((likes / react_count) * 100.0) if react_count > 0 else 0
      data = {
        "like_percent": like_percent,
      }

      return JsonResponse(data)

    return redirect(reverse("videos:watch", args=(media.uuid_code)))


class ToggleSubscription(LoginRequiredMixin, View):
  def post(self, request, *args, **kwargs):
    channel_id = self.kwargs.get("id", None)
    if not channel_id:
      return HttpResponseBadRequest()

    origin_media = self.request.POST.get("media_id", None)
    if origin_media and origin_media.isnumeric():
      origin_media = int(origin_media)
    else:
      origin_media = None

    media_item = Media.objects.filter(id=origin_media).first()
    sub, created = MediaSubscription.objects.get_or_create(subscriber=request.user, subbed_id=channel_id, defaults={"origin_media": media_item})
    print(sub)
    if not created:
      sub.delete()

    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    #if request.is_ajax():
    if is_ajax:
      data = {
      }

      return JsonResponse(data)

    return redirect(request.META.get("HTTP_REFERER", "/"))

