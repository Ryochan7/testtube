from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from .models import SiteUser

class SiteUserAdmin(UserAdmin):
  model = SiteUser

  def get_fieldsets(self, request, obj=None):
    if obj:
      current_fieldsets = []
      for item in UserAdmin.fieldsets:
        field_options = dict(item[1])

        if item[0] == None:
          fields = list(item[1]["fields"])
          fields.append("profile_image")
          field_options.update({"fields": tuple(fields)})

        current_fieldsets.append((item[0], field_options,))
    else:
      current_fieldsets = self.add_fieldsets + (
        ("Other", {"fields": ["profile_image"]}),
      )

    return current_fieldsets


admin.site.register(SiteUser, SiteUserAdmin)

