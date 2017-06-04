from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from django.template import RequestContext
from django.views import generic
from django.core.urlresolvers import reverse, resolve


def index(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            return HttpResponseRedirect('/upload-success')

    else:
        form = UploadFileForm()
    return render(request,'image_compare/index.html', {'form':form})

# Create your views here.
