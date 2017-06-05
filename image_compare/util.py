
from .models import ImageHistogram, BAND_GROUPS
import re
from PIL import Image
import math
import hashlib
from os import listdir,remove
from django.core.files.uploadedfile import UploadedFile
import numpy

IMAGE_DIR='images/'

def load_initial_images():
    histograms = ImageHistogram.objects.all()
    db_files = []
    for hist in histograms:

        print(hist.filename)
        db_files.append(hist.filename)

    on_disk = listdir(IMAGE_DIR)

    for f in on_disk:
        if f not in db_files:
            hasher = hashlib.md5()
            extension = re.search(r'\.(\w+)$',f)
            if extension:
                extension = extension.group(1)
            else:
                extension = 'unk'
            if_chunks = []
            with open("%s%s" % (IMAGE_DIR,f), 'rb') as ifh:
                for chunk in iter(lambda: ifh.read(UploadedFile.DEFAULT_CHUNK_SIZE), b""):
                    hasher.update(chunk)
                    if_chunks.append(chunk)
            remove("%s%s" % (IMAGE_DIR,f))

            new_filename = '%s.%s' % (hasher.hexdigest(),extension)
            with open("%s%s" % (IMAGE_DIR,new_filename), 'wb+') as ofh:
                for chunk in if_chunks:
                    ofh.write(chunk)

            calculate_histogram(new_filename, save_to_db=True)

def compare_images(h1,h2):
    def sum_array(arr):
        sum = 0
        for a in arr:
            sum+=a
        return sum

    h1_buckets = []
    h2_buckets = []

    # Concatenate previously calcuated band histogram data in order
    h1_buckets.extend(h1.red_band)
    h2_buckets.extend(h2.red_band)
    h1_buckets.extend(h1.green_band)
    h2_buckets.extend(h2.green_band)
    h1_buckets.extend(h1.blue_band)
    h2_buckets.extend(h2.blue_band)
    h1_buckets.extend(h1.alpha_band)
    h2_buckets.extend(h2.alpha_band)

    if len(h1_buckets) != len(h2_buckets):
        raise Exception("Non matching band data")


    bucket_len = len(h1_buckets)
    # Find te difference between each band bucket grouped by color and sum up the result
    # The smaller the result, the more similar the images are
    return sum_array([abs(h1_buckets[i] - h2_buckets[i]) for i in range(0,bucket_len)])


def find_similar(file1):

    histograms_on_file = ImageHistogram.objects.all()
    cur_histogram = calculate_histogram(file1)

    similarity_lookup = {}
    threshold = None
    similar_images = []
    for h in histograms_on_file:
        s = compare_images(cur_histogram, h)
        if s in similarity_lookup:
            similarity_lookup[s].append(h.filename)
        else:
            similarity_lookup[s] = [h.filename]


    #sorted_keys =







def calculate_histogram(image_file,save_to_db=False):
    # Open an image file
    full_filepath = "%s%s" % (IMAGE_DIR, image_file)
    image = Image.open(full_filepath)
    # Get the number of pixels so that the histograms can be normalized
    total_pixels = image.height * image.width
    # Split the image into bands.  This creates one image for each band
    bands = image.split()
    band_order = ['red','green','blue','alpha']
    # Make buckets for each band.  This will be used to count groups of similarly colored pixels
    buckets = {band_order[i]: band for i,band in enumerate(bands)}


    for color,band in buckets.items():
        band_buckets = [0 for x in range(0,BAND_GROUPS)]
        # Make a histogram for each band.
        histogram = band.histogram()

        if BAND_GROUPS > len(histogram) or len(histogram) % BAND_GROUPS != 0 or BAND_GROUPS <= 0:
            raise Exception("Invalid # of band groups")
        interval = int(len(histogram)/BAND_GROUPS)
        start_idx=0
        end_idx=interval
        i=0
        print("LEN HISTOGRAM: %s " % len(histogram))
        while end_idx <= len(histogram):
            # Sum up the pixel counts for range start_idx to end_idx
            for pixel_val in histogram[start_idx:end_idx]:
                band_buckets[i] += pixel_val
            # Divide each band bucket by the number of pixels in the image to normalize it
            band_buckets[i] /= total_pixels
            start_idx = end_idx
            end_idx += interval
            i+=1

        buckets[color] = band_buckets
    # assuming 4 band groups and an alpha channel, buckets should now look something like this:
    # buckets['red'] = [r1,r2,r3,r4]
    # buckets['green'] = [g1,g2,g3,g4]
    # buckets['blue'] = [b1,b2,b3.b4]
    # buckets['alpha'] = [a1,a2,a3,a4]
    hist_model = ImageHistogram(filename=image_file,num_bands=len(bands),total_pixels=total_pixels,
      red_band=buckets['red'], green_band=buckets['green'], blue_band=buckets['blue'],
      alpha_band=buckets.get('alpha',[0 for x in range(0,BAND_GROUPS)])
    )
    if save_to_db:
        hist_model.save()

    return hist_model

def handle_uploaded_file(f):
    filename = f.name
    extension = re.search(r'(\w+)$',f.name)
    if extension:
        extension = extension.group(1)
    else:
        extension = '.unk'
    hasher = hashlib.md5()

    for chunk in f.chunks():
        hasher.update(chunk)
    filename = "%s.%s" % (hasher.hexdigest(),extension)
    with open("%s%s" % (IMAGE_DIR,filename), 'wb+') as df:
        for chunk in f.chunks():
            df.write(chunk)

    return calculate_histogram(filename)
