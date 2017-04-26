import argparse
import flickrapi
# import code
# import json
import os
import pyexiv2
# import time
import urllib
import webbrowser


class FlickrSavr(object):
    """This is a digital preservation experiment.  It crawls your Flickr
    Photos and saves them to disk with all the Flickr metadata stored
    in the EXIF.  The idea here is, most preservation methods keep the
    photos and then keep a separate database (in whatever format)
    elsewhere.  I thought I could have all the date stored in the
    photo so that it is not only coupled with the primary data but
    could be reconstructed from arbitrary collections of photos across
    people.  It's just an experiment...it's not complete and I make no
    promises.

    3600 queries per hour is all thats allowed (thats 1 query per
    second). Each photo takes 3 queries to get it's metadata...so
    that's a cap of 1200 photos per hour.  It takes (by rough estimate)
    3 seconds to query 3 times, download, and write to disk.  So by
    most estimates you won't overrun the limit...that said, we'll sleep
    200 ms between photos just to be nice.

    """

    def __init__(self,
                 key,
                 secret,
                 nsid,
                 basepath,
                 verbose,
                 force):
        """do

        Arguments:
        - `key`:
        - `secret`:
        - `ndsid`:
        - `basepath`:
        - `verbose`:
        - `force`:
        """
        # auth
        self.api_key = key
        self.api_secret = secret
        self.nsid = nsid
        self.basepath = os.path.join(basepath, "nsid", self.nsid)
        self.verbose = not verbose
        self.force = force

        self.photo_count = 0
        self.photo_page = 0
        self.photo_total = 0
        self.per_page = 500

        self.flickr = flickrapi.FlickrAPI(self.api_key,
                                          self.api_secret,
                                          format='parsed-json')

        # Only do this if we don't have a valid token already
        if not self.flickr.token_valid(perms=unicode('write')):

            # Get a request token
            self.flickr.get_request_token(oauth_callback='oob')

            # Open a browser at the authentication URL. Do this however
            # you want, as long as the user visits that URL.
            authorize_url = self.flickr.auth_url(perms=unicode('write'))
            webbrowser.open_new_tab(authorize_url)

            # Get the verifier code from the user. Do this however you
            # want, as long as the user gives the application the code.
            verifier = unicode(raw_input('Verifier code: '))

            # Trade the request token for an access token
            self.flickr.get_access_token(verifier)

        # dir
        if not os.path.exists(self.basepath):
            os.makedirs(self.basepath)

        # search: this has a 'pages' field with how many photos left
        # accounting per page..max is 500
        extras = "%s,%s,%s,%s,%s,%s,%s,%s," % ("url_o",
                                               "geo",
                                               "tags",
                                               "machine_tags",
                                               "views",
                                               "description",
                                               "date_upload",
                                               "date_taken")

        photos = self.flickr.photos_search(user_id=self.nsid,
                                           per_page=self.per_page,
                                           extras=extras)
        photos = photos['photos']

        self.photo_total = photos['perpage'] * photos['pages']
        self.photo_page = 0

        for i in range(photos['perpage']):
            self.photo_count = i
            photo = photos['photo'][i]
            self.get_photo(photo)

        # this page counter is for the next page actually
        for page in range(photos['pages'])[1:]:
            self.photo_page = page
            photos = self.flickr.photos_search(user_id=self.nsid,
                                               page=str(page),
                                               per_page=self.per_page,
                                               extras=extras)
            photos = photos['photos']
            for i in range(photos['perpage']):
                self.photo_count = i
                photo = photos['photo'][i]
                self.get_photo(photo)
        return

    def get_photo(self, photo):
        """Get the data around a photo.

        Arguments:
        - `self`:
        - `photo`:
        """

        # Check if we have it already
        url = photo['url_o']
        fname = os.path.join(self.get_date_path(photo),
                             photo['id'] + url[-4:])
        exists = not self.force and os.path.isfile(fname)
        if exists:
            self.print_status_count(True)
            return

        # get image
        resp = urllib.urlopen(url)
        image_data = resp.read()

        # Open output file in binary mode, write, and close.
        f = open(fname, 'wb')
        f.write(image_data)
        f.close()
        self.print_status_count()

        # get more metadata
        favorites = []
        favs = self.flickr.photos_getFavorites(photo_id=photo['id'])
        for person in favs['photo']['person']:
            s = "Flickr.favorites:%s:%s:%s" % (person['username'],
                                               person['nsid'],
                                               person['favedate'])
            favorites.append(s)

        comments = []
        comms = self.flickr.photos_comments_getList(photo_id=photo['id'])
        try:
            for comment in comms['comments']['comment']:
                c = "Flickr.comments:%s:%s:%s:%s" % (comment['author'],
                                                     comment['authorname'],
                                                     comment['datecreate'],
                                                     comment['_content'])
                comments.append(c)
        except:
            pass
        pools = []
        # this call failed...maybe try to wrap all the bad ids
        # somewhere for later handling
        pool = self.flickr.photos_getAllContexts(photo_id=photo['id'])
        try:
            for sets in pool['set']:
                c = "Flickr.sets:%s:$s" % (sets['title'],
                                           sets['id'])
                pools.append(c)
        except:
            pass
        # write exif
        metadata = pyexiv2.ImageMetadata(fname)
        metadata.read()
        key = 'Iptc.Application2.Keywords'
        vals = ["Flickr.id:%s" % photo['id'],
                "Flickr.owner:%s" % self.nsid,
                "Flickr.title:%s" % photo['title'],
                "Flickr.description:%s" % photo['description']['_content'],
                "Flickr.isfamily:%d" % photo['isfamily'],
                "Flickr.isfriend:%d" % photo['isfriend'],
                "Flickr.views:%s" % photo['views'],
                "Flickr.date_upload:%s" % photo['dateupload'],
                "Flickr.date_taken:%s" % photo['datetaken']]
        if ('latitude' in photo and 'longitude' in photo):
            coords = ["Flickr.latitude:%s" % photo['latitude'],
                      "Flickr.longitude:%s" % photo['longitude']]
            vals += coords
        if ('accuracy' in photo):
            accuracy = ["Flickr.accuracy:%s" % photo['accuracy']]
            vals += accuracy
        if ('tags' in photo):
            tags = ["Flickr.tags:%s" % photo['tags']]
            vals += tags
        # join all into vals
        vals.extend(favorites)
        metadata[key] = vals
        metadata.iptc_charset = 'utf-8'
        metadata.write()

    def get_date_path(self, photo):
        datetaken = photo['datetaken']
        date = datetaken.split(' ')[0]
        parsed = date.split('-')
        path = os.path.join(self.basepath, parsed[0], parsed[1], date)
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def print_status(self, s):
        if self.verbose:
            print s
        return

    def print_status_count(self, exists=False):
        condition = ""
        if exists:
            condition = "(file exists)"
        if self.verbose:
            self.print_status("%s / %s %s" %
                              (1 + self.photo_count + (self.per_page *
                                                       self.photo_page),
                               self.photo_total,
                               condition))
        return


def main():
    desc = 'Download a Flickr Account.'
    parser = argparse.ArgumentParser(prog='FlickrSavr',
                                     usage='%(prog)s key secret nsid',
                                     description=desc,
                                     epilog='thats how its done.')
    parser.add_argument('key', help='Flickr API Key')
    parser.add_argument('secret', help='Flickr API Secret')
    parser.add_argument('nsid', help='Flickr Account NSID')
    parser.add_argument('-b', '--basepath',
                        nargs=1,
                        default='',
                        help='Basedirectory to use for storing files.')
    parser.add_argument("-f",
                        "--force",
                        help="Force download if file already exists. ",
                        action="store_true")
    parser.add_argument("-q",
                        "--quiet",
                        help="increase output verbosity",
                        action="store_true")
    args = parser.parse_args()
    FlickrSavr(args.key, args.secret, args.nsid, args.basepath[0],
               args.quiet, args.force)


if __name__ == "__main__":
    main()
