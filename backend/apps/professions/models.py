from django.db import models
from common.db.models import BaseUUIDModel


class Profession(BaseUUIDModel):
    slug = models.SlugField(unique=True)  # ex: physio, nutrition, psychology
    display_name = models.CharField(max_length=80)

    class Meta:
        db_table = "profession"
        ordering = ["display_name"]

    def __str__(self) -> str:
        return self.display_name
