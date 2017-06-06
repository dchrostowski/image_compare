from django.db import models
from django.contrib.postgres.fields import ArrayField

# BAND_GROUPS is an arbitrary integer that will determine how
# finely bands will be grouped. If BAND_GROUPS == 4, it will
# create 4 groups for a given color band:
# Group 1: pixels in value range [0-63]
# Group 2: pixels in value range [64-127]
# Group 3: pixels in value range [128-191]
# Group 4: pixels in value range [192-256]

# By adding more groups, you sacrifice efficiency for accuracy
BAND_GROUPS = 4
default_val = [0 for x in range(0,BAND_GROUPS)]
# Create your models here.

class ImageMetadata(models.Model):
    filename=models.CharField(max_length=100,primary_key=True)
    num_bands=models.IntegerField(null=False,blank=False)
    height=models.IntegerField(null=False,blank=False)
    width=models.IntegerField(null=False,blank=False)
    total_pixels=models.IntegerField(null=False,blank=False)
    red_band = ArrayField(models.DecimalField(max_digits=10,decimal_places=4,null=False,blank=False),size=BAND_GROUPS,default=default_val)
    green_band = ArrayField(models.DecimalField(max_digits=10,decimal_places=4,null=False,blank=False),size=BAND_GROUPS,default=default_val)
    blue_band = ArrayField(models.DecimalField(max_digits=10,decimal_places=4,null=False,blank=False),size=BAND_GROUPS,default=default_val)
    vectors = ArrayField(models.DecimalField(max_digits=10,decimal_places=4,null=False,blank=False), default=[0.0])
    norm = models.DecimalField(max_digits=10,decimal_places=4,null=False,blank=False)
