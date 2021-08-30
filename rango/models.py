from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify


class Category(models.Model):
    """
    Stores a category of Page model.
    """
    name = models.CharField(max_length=128, unique=True)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        if self.views<0:
            self.views = 0
        super(Category, self).save(*args, **kwargs)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Page(models.Model):
    """
    Stores a page that contains title and url of website.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    title = models.CharField(max_length=128)
    url = models.URLField(max_length=200)
    views = models.IntegerField(default=0)
    last_visit = models.DateTimeField(default=timezone.now())

    def __str__(self):
        return self.title


class UserProfile(models.Model):
    """
    Stores the website and picture of a User.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    website = models.URLField(blank=True)
    picture = models.ImageField(upload_to ='profile_images', blank=True)

    def __str__(self):
        return self.user.username
