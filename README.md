# Flickr Savr

Save photos from Flickr to your disk with metadata.

## About

This is a digital preservation experiment.  It crawls your Flickr
Photos and saves them to disk with all the Flickr metadata stored in
the EXIF.  The idea here is, most preservation methods keep the photos
and then keep a separate database (in whatever format) elsewhere.  I
thought I could have all the date stored in the photo so that it is
not only coupled with the primary data but could be reconstructed from
arbitrary collections of photos across people.  It's just an
experiment...it's not complete and I make no promises.

## Dependencies

* Python 2.7
* [https://pypi.python.org/pypi/flickrapi](https://pypi.python.org/pypi/flickrapi)
* [http://tilloy.net/dev/pyexiv2/](http://tilloy.net/dev/pyexiv2/)

## Limits

3600 queries per hour is all thats allowed. Thats 1 query per
second. Each photo takes 3 queries to get it's metadata...so
that's a cap of 1200 photos per hour.  It takes, by rough
estimate, 3 seconds to query 3 times, download, and write to disk.
So by most estimates you won't overrun the limit...that said,
we'll sleep 200 ms between photos just to be nice
