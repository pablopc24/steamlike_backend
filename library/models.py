from django.db import models
from django.contrib.auth.models import User


class Entry(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    external_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255, default="")
    content = models.TextField(default="", blank=True)

    def __str__(self):
        return f"{self.external_id} ({self.title})"

    def external_id_length(self):
        value = self.external_id

        if value is None:
            return 0

        if not isinstance(value, str):
            raise TypeError("external_id must be a string or None")

        return len(value)
