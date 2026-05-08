from django.db import models
from django.contrib.auth.models import User


class Entry(models.Model):
    title = models.CharField(max_length=255, default='')
    content = models.TextField(blank=True, default='')
    external_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    hours_played = models.IntegerField(default=0)
    notes = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"{self.external_id} ({self.title})"

    def external_id_length(self):
        value = self.external_id

        if value is None:
            return 0

        if not isinstance(value, str):
            raise TypeError("external_id must be a string or None")

        return len(value)
