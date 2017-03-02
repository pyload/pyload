# -*- coding: utf-8 -*-

import re

from ..internal.misc import json, uniqify
from ..internal.SimpleCrypter import SimpleCrypter


class ImgurCom(SimpleCrypter):
    __name__ = "ImgurCom"
    __type__ = "crypter"
    __version__ = "0.61"
    __status__ = "testing"

    __pattern__ = r'https?://(?:www\.|m\.)?imgur\.com/(a|gallery|)/?\w{5,7}'
    __config__ = [("activated", "bool", "Activated", True),
                  ("use_premium", "bool", "Use premium account if available", True),
                  ("folder_per_package", "Default;Yes;No",
                   "Create folder for each package", "Default"),
                  ("max_wait", "int", "Reconnect if waiting time is greater than minutes", 10)]

    __description__ = """Imgur.com decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("nath_schwarz", "nathan.notwhite@gmail.com"),
                   ("nippey", "matthias.nippert@gmail.com")]

    NAME_PATTERN = r'(?P<N>.+?) - .*?Imgur'
    LINK_PATTERN = r'i\.imgur\.com/\w{7}s?\.(?:jpeg|jpg|png|gif|apng)'

    """ Imgur may only show the first 10 images of a gallery. The remaining bits may be found here: """
    GALLERY_JSON = "http://imgur.com/ajaxalbums/getimages/%s/hit.json?all=true"

    def sanitize(self, name):
        """ Turn Imgur Gallery title into a safe Package and Folder name """
        keepcharacters = (' ', '\t', '.', '_')
        replacecharacters = (' ', '\t')
        return "".join(c if c not in replacecharacters else '_' for c in name.strip(
        ) if c.isalnum() or c in keepcharacters).strip('_')

    def get_ids_from_json(self):
        """ Check the embedded JSON and if needed the external JSON for more images """

        # Greedy re should match the closing bracket of json assuming JSON data
        # is placed on a single line
        m = re.search(r"\simage\s+:\s+({.*})", self.data)
        if m is not None:
            embedded_json = json.loads(m.group(1))

            # Extract some metadata (ID, Title, NumImages)
            gallery_id = embedded_json['hash']
            self.gallery_name = self.sanitize(
                _("%s_%s") %
                (gallery_id, embedded_json['title']))
            self.total_num_images = int(embedded_json['num_images'])

            # Extract images
            images = dict((e['hash'], e['ext'])
                          for e in embedded_json['album_images']['images'])

            self.log_debug(
                "Found %s of %s expected links in embedded JSON" %
                (len(images), self.total_num_images))

            # Depeding on the gallery, the embedded JSON may not contain all image information, then we also try the external JSON
            # If this doesn't help either (which is possible),... TODO: Find
            # out what to do
            if len(images) < self.total_num_images:
                external_json = json.loads(
                    self.load(
                        self.GALLERY_JSON %
                        gallery_id))

                try:
                    images = dict((e['hash'], e['ext'])
                                  for e in external_json['data']['images'])
                    self.log_debug(
                        "Found %s of %s expected links in external JSON" %
                        (len(images), self.total_num_images))

                except (KeyError, TypeError):
                    self.log_debug(
                        "Could not extract links from external JSON")
                    # It is possible that the returned JSON contains an empty
                    # 'data' section. We ignore it then.

            return images

        self.log_debug("Could not find embedded JSON")

        return {}

    def get_indirect_links(self, links_direct):
        """ Try to find a list of all images and add those we didn't find already """

        # Extract IDs of known direct links
        ids_direct = set(
            [l for link in links_direct for l in re.findall(r'(\w{7})', link)])

        # Get filename extensions for new IDs
        ids_json = self.get_ids_from_json()
        ids_indirect = [id for id in ids_json.keys() if id not in ids_direct]

        # No additional images found
        if len(ids_indirect) == 0:
            return []

        # Translate new IDs to Direct-URLs
        return map(lambda id: "http://i.imgur.com/%s%s" %
                   (id, ids_json[id]), ids_indirect)

    def setup(self):
        self.gallery_name = None
        self.total_num_images = 0

    def get_links(self):
        """ Extract embedded links from HTML // then check if there are further images which will be lazy-loaded """

        f = lambda url: "http://" + re.sub(r'(\w{7})s\.', r'\1.', url)
        direct_links = uniqify(
            map(f, re.findall(self.LINK_PATTERN, self.data)))

        # Imgur Galleryies may contain more images than initially shown. Find
        # the rest now!
        try:
            indirect_links = self.get_indirect_links(direct_links)
            self.log_debug(
                "Found %s additional links" % (len(indirect_links)))

        except (TypeError, KeyError, ValueError), e:
            # Fail gracefull as we already had some success
            self.log_error(
                _("Processing of additional links unsuccessful - %s: %s") %
                (type(e).__name__, str(e)))
            indirect_links = []

        # Check if all images were found and inform the user
        num_images_found = len(direct_links) + len(indirect_links)
        if num_images_found < self.total_num_images:
            self.log_error(
                _("Could not save all images of this gallery: %s/%s") %
                (num_images_found, self.total_num_images))

        # If we could extract a name, use this to create a specific package
        if self.gallery_name:
            self.packages.append(
                (self.gallery_name,
                 direct_links + indirect_links,
                 self.gallery_name))
            return []

        else:
            return direct_links + indirect_links
