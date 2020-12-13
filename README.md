# Flickr Savr

Save photos from Flickr to your disk with metadata embedded in the
photos.

## About

This is a digital preservation experiment.  It crawls your Flickr
Photos and saves them to disk with all the Flickr metadata stored in
the EXIF.  The idea here is, most preservation methods keep the photos
and then keep a separate database (in whatever format) elsewhere.  I
thought I could have all the data stored in the photo so that it is
not only coupled with the primary data but could be reconstructed from
arbitrary collections of photos across people.  It's just an
experiment...it's not complete and I make no promises.

## Version 2 

Version 2 makes an explicit XMP namespace (with RDF XML) and stores
all the metadata is neatly stored there. Version 1 just added well
formatted strings to the ICTP keyword array. Not only was this messier
and unorganized like that drawer in your kitchen, it had a consequence
on general photo search tools.  As a result, **if you used Version 1**
leave that old photos dir alone and make a new one for Version 2.
They are incompatible.

## Running this

You'll need to make your own [Flickr API Key and
Seceret](https://www.flickr.com/services/apps/by/ayman).  You'll also
need to look up your NSID.  You can find it by visiting a [URL in the
Flickr App
Garden](https://www.flickr.com/services/api/explore/flickr.profile.getProfile)
listed as *Your user ID*.

You can run the script as:
```
python flickr-savr.py -b PHOTODIR YOURAPIKEY YOURAPISECRET YOURNSID
```

## Dependencies

* Python 3
* [https://pypi.python.org/pypi/flickrapi](https://pypi.python.org/pypi/flickrapi)
  Can be pip installed.

## MacOS

I think you need all this stuff with [*homebrew*](https://brew.sh):

```
brew install boost-python3 gexiv2 pygobject3
```

And if you are using a VENV and notice it cant find the `gi` package, you might need to point the PYTHONPATH:

```
export PYTHONPATH=/usr/local/lib/python3.9/site-packages
```

That's mine, yours might be different.

## Limits

3600 queries per hour is all thats allowed. Thats 1 query per
second. Each photo takes 3 queries to get its metadata...so
that's a cap of 1200 photos per hour.  It takes, by rough
estimate, 3 seconds to query 3 times, download, and write to disk.
So by most estimates you won't overrun the limit...that said,
we'll sleep 200 ms between photos just to be nice
