from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from .util import calculate_metadata, handle_uploaded_file,load_initial_images
from django.template import RequestContext
from django.views import generic
from django.core.urlresolvers import reverse, resolve
from django.conf import settings
from datetime import datetime
import random
import string
BLOCKSIZE = 65536
import re

def index(request):
    load_initial_images()
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if not request.session.session_key:
            request.session.save()
        if form.is_valid():
            similar_images = handle_uploaded_file(request.FILES['file'],request.session.session_key)
            search_img = similar_images[0]
            similar_images = similar_images[1:]
            return upload_success(request,search_img,similar_images)

    else:
        form = UploadFileForm()
    return render(request,'image_compare/index.html', {'form':form})

def upload_success(request,query,data):
    return render(request,'image_compare/success.html', {'index':'/', 'query':query, 'files':data})
