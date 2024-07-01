from uuid import uuid4

import shortuuid
from django.contrib.auth.models import User
from django.db import models

# Create your models here.


def generate_uuid():
    # SAFETY: This is using urandom. In most modern OS, this is cryptographically secure.
    return shortuuid.encode(uuid4())


class CommonBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    uuid = models.CharField(max_length=42, editable=False, unique=True, default=generate_uuid)

    class Meta:
        abstract = True

    def _str_(self):
        return self.uuid


class BlogPost(CommonBaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    youtube_title = models.CharField(max_length=300)
    youtube_link = models.URLField()
    generated_contend = models.TextField()
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.youtube_title
