from django.contrib import admin
from .models import Entry

@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ("external_id", "title", "owner")
    search_fields = ("external_id", "title")
