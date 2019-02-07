import re

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

re_triminnertext = re.compile(r"\n\s*")

@register.filter
@stringfilter
def spacelesstext(value):
  final = re_triminnertext.sub(" ", value).strip()
  return final

