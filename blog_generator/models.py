from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class BlogPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    youtube_title = models.CharField(max_length=300)
    youtube_link = models.URLField()
    generated_contend = models.TextField()
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.youtube_title
