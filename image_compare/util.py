
from .models import ImageMetadata, BAND_GROUPS
import re
from PIL import Image
import math
import hashlib
from os import listdir,remove
import os
from django.core.files.uploadedfile import UploadedFile
import numpy
from shutil import copyfile, rmtree

IMAGE_DIR='images/'
SESSION_DIR = 'image_compare/static/sessions/'
PUBLIC_SESSION_DIR = '/static/sessions/'

def load_initial_images():
    histograms = ImageMetadata.objects.all()
    db_files = []
    on_disk = listdir(IMAGE_DIR)
    for hist in histograms:
        # Delete any image metadata that are not on disk
        if hist.filename not in on_disk:
            hist.delete()
        else:
            db_files.append(hist.filename)

    for f in on_disk:
        # Rename and add any untracked files to database
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
            # Caclulate metadata and save to database
            calculate_metadata(new_filename, save_to_db=True)

# Normalized cross correlation comparison
def compare_images_via_cross_correlation(h1,h2):
    h1_vectors = [numpy.float64(float(v)) for v in h1.vectors]
    h2_vectors = [numpy.float64(float(v)) for v in h2.vectors]
    return numpy.dot(h1_vectors / numpy.float64(float(h1.norm)), h2_vectors / numpy.float64(float(h2.norm)))

# Will compare using normalized cross correlation or color histogram
# normalized cross correlation is only valid for images with identical dimensions
# Will fallback to histogram method if the images are not compatible
def compare_images_via_histogram(h1,h2):
    h1_band_groups = []
    h2_band_groups = []

    band_attrs = ['red_band','green_band','blue_band']

    # Concatenate previously calcuated band histogram data in order
    for ba in band_attrs:
        h1_band_groups.extend(getattr(h1,ba))
        h2_band_groups.extend(getattr(h2,ba))

    if len(h1_band_groups) != len(h2_band_groups):
        raise Exception("Non matching band data")


    group_len = len(h1_band_groups)
    # Find te difference between each band bucket grouped by color and sum up the result
    # The smaller the result, the more similar the images are
    return sum([abs(float(h1_band_groups[i]) - float(h2_band_groups[i])) for i in range(0,group_len)])


def find_similar(file1,skey):
    # Get metadata from database
    metadata_on_file = ImageMetadata.objects.all()
    cur_metadata = calculate_metadata(file1,save_to_db=False)
    session_dir = "%s%s" % (SESSION_DIR,skey)
    try:
        rmtree(session_dir)
    except FileNotFoundError as e:
        pass

    histogram_lookup = {}
    sim_lookup = {}

    similar_images = []
    for m in metadata_on_file:
        # compare by cross correlation if height and width of images are the same
        if m.height == cur_metadata.height and m.width == cur_metadata.width:
            s = compare_images_via_cross_correlation(cur_metadata,m)
            if s in sim_lookup:
                sim_lookup[s].append(m.filename)
            else:
                sim_lookup[s] = [m.filename]
        # otherwise compare with histogram method
        else:
            s = compare_images_via_histogram(cur_metadata, m)
            if s in histogram_lookup:
                histogram_lookup[s].append(m.filename)
            else:
                histogram_lookup[s] = [m.filename]


    histogram_scores = sorted([s for s in histogram_lookup.keys()])
    worst = histogram_scores[-1] or 1

    # normalize histogram scores to create a curved percentage where worst score is 0% similar; 0 = 100% similar
    for score in histogram_lookup.keys():
        normalized = 1-(score/worst)
        files = histogram_lookup[score]
        if normalized in sim_lookup:
            sim_lookup[normalized].extend(files)
        else:
            sim_lookup[normalized] = files

    scores = sorted(sim_lookup.keys(),reverse=True)


    # Performs O(n) lookup of smallest values in an array
    best_scores = scores[:3]
    best_images = []
    for b in best_scores:
        best_images.extend(sim_lookup[b])
    # If there were any ties in similarity, more than three images could have been added
    best_images = best_images[:3]


    # Create a static directory named with session key, copy images to that directory
    try:
        os.mkdir(session_dir)
        os.chmod(session_dir,666)
        os.mkdir("%s/%s" % (session_dir, 'query'))
        os.chmod("%s/%s" % (session_dir, 'query'), 666)
    except FileExistsError as e:
        rmtree(session_dir)
        os.mkdir(session_dir)

    copied_files = []

    # copy uploaded image to session directory
    copyfile("%s%s" % (IMAGE_DIR,file1), "%s/query/%s" % (session_dir,file1))
    copied_files.append("%s%s/query/%s" % (PUBLIC_SESSION_DIR,skey,file1))

    # copy all matched files over to session directory
    for img in best_images:
        dst = "%s/%s" % (session_dir,img)
        public_dst = "%s%s/%s" % (PUBLIC_SESSION_DIR, skey, img)
        copyfile("%s%s" % (IMAGE_DIR,img), dst)
        copied_files.append(public_dst)


    return copied_files



def calculate_vectors(image):
    vectors = []
    # Make image smaller for efficiency
    smaller_image = image.resize((int(image.width/8),int(image.height/8)))
    for t in smaller_image.getdata():
        v = numpy.average(t)
        vectors.append(v)
    norm = numpy.linalg.norm(vectors,2)
    return (vectors,norm)


#  will be used for comparing with one of two methods: color histogram or normalized cross correlation
def calculate_metadata(image_file,save_to_db=False):
    # Open an image file
    full_filepath = "%s%s" % (IMAGE_DIR, image_file)
    image = Image.open(full_filepath)
    # Convert all images to RGB
    image = image.convert("RGB")
    # Get the number of pixels so that the histograms can be normalized
    total_pixels = image.height * image.width
    # Split the image into bands.  This creates one image for each band
    bands = image.split()
    band_order = ['red','green','blue']
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
        while end_idx <= len(histogram):
            # Sum up the pixel counts for range start_idx to end_idx
            for pixel_val in histogram[start_idx:end_idx]:
                band_buckets[i] += pixel_val
            # Divide each band bucket by the number of pixels in the image to normalize it
            # Multiply by 1000 so the numbers aren't ridiculously tiny
            band_buckets[i] /= total_pixels * 1000
            start_idx = end_idx
            end_idx += interval
            i+=1

        buckets[color] = band_buckets
    # assuming BAND_GROUPS=4, buckets should now look something like this:
    # buckets['red'] = [r1,r2,r3,r4]
    # buckets['green'] = [g1,g2,g3,g4]
    # buckets['blue'] = [b1,b2,b3.b4]

    # Used for normalized cross correlation.
    vectors, norm = calculate_vectors(image)
    image_metadata = ImageMetadata(filename=image_file,height=image.height,width=image.width,num_bands=len(bands),total_pixels=total_pixels,
      red_band=buckets['red'], green_band=buckets['green'], blue_band=buckets['blue'],vectors=vectors, norm=norm)
    if save_to_db:
        # save model to database
        image_metadata.save()

    return image_metadata

# Handles uploaded file, performs a hash function to name file so there aren't any duplicates
def handle_uploaded_file(f,skey):
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

    return find_similar(filename,skey)
