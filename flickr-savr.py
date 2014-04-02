import urllib
import flickrapi
import pyexiv2
import json
import time
import os

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
                 api_key, 
                 secret, 
                 nsid, 
                 verbose=False, 
                 sleep_time=0.200):
        """do
        
        Arguments:
        - `api_key`:
        - `secret`:
        - `ndsid`:
        - `verbose`:
        - `sleep_time`:
        """        
        ## auth
        self.api_key = api_key
        self.secret = secret
        self.nsid = nsid
        self.flickr = flickrapi.FlickrAPI(api_key, secret, format='json')
        ## dir
        if not os.path.exists(self.nsid):
            os.makedirs(self.nsid)
        (token, frob) = self.flickr.get_token_part_one(perms='write')
        if not token: 
            raw_input("Press ENTER after you authorized this program")
        self.flickr.get_token_part_two((token, frob))

        ## search: this has a 'pages' field with how many photos left
        ## accounting per page..max is 500
        extras = "%s,%s,%s,%s,%s,%s,%s,%s," % ("url_o",
                                               "geo",
                                               "tags",
                                               "machine_tags",
                                               "views",
                                               "description",
                                               "date_upload",
                                               "date_taken")
        photos = self.flickr.photos_search(user_id=self.nsid, 
                                           per_page='1', 
                                           extras=extras)
        jphotos = json.loads(photos[14:-1])
        for i in range(jphtos['perpage']):
            photo = jphotos['photos']['photo'][i]
            self.get_photo(photo)
            time.sleep(sleep_time)
        ## this page counter is for the next page actually
        for page in range(jphotos['pages'])[1:]:
            photos = self.flickr.photos_search(user_id=self.nsid, 
                                               page=str(page),
                                               per_page='1', 
                                               extras=extras)
            jphotos = json.loads(photos[14:-1])
            for i in range(jphtos['perpage']):
                photo = jphotos['photos']['photo'][i]
                self.get_photo(photo)
                time.sleep(sleep_time)
        return

    def get_photo(self, photo):
        """Get the data around a photo.
        
        Arguments:
        - `self`:
        - `photo`:
        """        
                
        ## get image
        url = photo['url_o']
        resp = urllib.urlopen(url)
        image_data = resp.read()
        fname = os.path.join(self.nsid, photo['id'] + url[-4:])
        # Open output file in binary mode, write, and close.
        f = open(fname, 'wb')
        f.write(image_data)
        f.close()

        ## get more metadata
        favorites = []
        f = self.flickr.photos_getFavorites(photo_id=photo['id'])
        favs = json.loads(f[14:-1])
        for person in favs['photo']['person']:
            s = "Flickr.favorites:%s:%s:%s" % (person['username'],
                                               person['nsid'], 
                                               person['favedate'])
            favorites.append(s)

        comments = []
        c = self.flickr.photos_comments_getList(photo_id=photo['id'])
        comms = json.loads(c[14:-1])
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
        p = self.flickr.photos_getAllContexts(photo_id=photo['id']);
        pool = json.loads(c[14:-1])
        try: 
            for sets in pool['set']:
                c = "Flickr.sets:%s:$s" % (sets['title'],
                                           sets['id'])
                pools.append(c)
        except:
            pass
        ## write exif
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
        if (photo.has_key('latitude') and
            photo.has_key('longitude')):
            coords = ["Flickr.latitude:%s" % photo['latitude'],	
                      "Flickr.longitude:%s" % photo['longitude']]
            vals += coords
        if (photo.has_key('accuracy')):    
            accuracy = ["Flickr.accuracy:%s" % photo['accuracy']]
            vals += accuracy
        if (photo.has_key('tags')):    
            tags = ["Flickr.tags:%s" % photo['tags']]
            vals += tags
        ## join all into vals
        vals.extend(favorites)
        metadata[key] = vals
        metadata.iptc_charset = 'utf-8'
        metadata.write()

def main():
    import getopt
    import sys
    options = getopt.getopt(sys.argv[1:],
                            'h, v',
                            ['help', 'verbose'])
    raw = False
    if len(options[-1]) is 0:
        print "I guess I need your NSID"
        sys.exit(0)
    verbose = False
    for option, value in options[0]:
        if option in ('-h', '--help'):
            if (len(options[-1]) is 0):
                print "Which nsid do you want?"
            else:
                print __doc__
            sys.exit(0)
        elif option in ('-v', '--verbose'):
            verbose = True
    # term = options[-1][0]
    api_key = ""
    secret = ""
    nsid = ""
    FlickrSavr(api_key, secret, nsid, verbose)

if __name__ == "__main__":
    main()
