from typing import final

from django.contrib import admin

from .models import Poster


@final
@admin.register(Poster)
class PosterAdmin(admin.ModelAdmin[Poster]):
    list_display = ("epds_code", "title")
