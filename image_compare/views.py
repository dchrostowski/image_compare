from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from .util import calculate_histogram, handle_uploaded_file,load_initial_images
from django.template import RequestContext
from django.views import generic
from django.core.urlresolvers import reverse, resolve
from datetime import datetime
import random
import string
BLOCKSIZE = 65536
import re





def index(request):
    load_initial_images()
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            histogram_data = handle_uploaded_file(request.FILES['file'])
            return upload_success(request,histogram_data)

    else:
        form = UploadFileForm()
    return render(request,'image_compare/index.html', {'form':form})

def upload_success(request,data):
    print(data)
    print(data.red_band)
    return render(request,'image_compare/success.html', {'index':'/', 'histogram_data':data})
# Create your views here.
