import base64
import os
import re
import urllib.parse
import urllib.request

from defusedxml.minidom import parseString as parse_xml

from pyload.core.utils.convert import to_str
from pyload.core.utils.fs import safename
from pyload.core.utils.web.purge import unescape as html_unescape

from ..base.container import BaseContainer


class NZB(BaseContainer):
    __name__ = "NZB"
    __type__ = "container"
    __version__ = "0.01"
    __status__ = "testing"

    __pattern__ = r"(?:file|https?)://.+\.nzb|(?!(?:file|https?)://).+\.nzb"
    __config__ = [
        ("enabled", "bool", "Activated", True),
        ("use_premium", "bool", "Use premium account if available", True),
        (
            "folder_per_package",
            "Default;Yes;No",
            "Create folder for each package",
            "Default",
        ),
    ]

    __description__ = """NZB container decrypter plugin"""
    __license__ = "GPLv3"
    __authors__ = [("GammaC0de", "nitzo2001[AT]yahoo[DOT]com")]

    CONTAINER_PATTERN = r"(?!(?:file|https?)://).+\.nzb"
    DECRYPTER_PATTERN = r"(?:file|https?)://.+\.nzb"

    def process(self, pyfile):
        if re.match(self.DECRYPTER_PATTERN, pyfile.url) is not None:
            self.log_error(self._("No plugin is associated with nzb"),
                           self._("Please go to plugin settings -> NZB and select your preferred plugin"))

            self.fail(self._("No plugin is associated with nzb"))

        elif re.match(self.CONTAINER_PATTERN, pyfile.url) is not None:
            return super().process(pyfile)

    def decrypt(self, pyfile):
        fs_filename = os.fsencode(pyfile.url)
        with open(fs_filename, mode="r", encoding="utf-8-sig") as fp:
            nzb_content = fp.read()

        pack_name = safename(self.generate_package_name(nzb_content) or pyfile.package().name)

        nzb_filename = os.path.join(
            self.pyload.tempdir, "tmp_{}.nzb".format(pack_name)
        )
        with open(nzb_filename, mode="w", encoding="utf-8-sig") as fp:
            fp.write(nzb_content)

        self.packages.append(
            (
                pack_name,
                ["file://{}".format(urllib.request.pathname2url(nzb_filename))],
                pack_name,
            )
        )

    def generate_package_name(self, nzb_content):
        try:
            dom = parse_xml(nzb_content)

        except Exception:
            self.log_error(self._("Error parsing NZB file"))
            return None

        else:
            for meta in dom.getElementsByTagName("meta"):
                if meta.getAttribute("type").lower() == "title":
                    title_text = "".join(
                        node.nodeValue for node in meta.childNodes
                        if node.nodeType == dom.TEXT_NODE
                    )
                    title = title_text.strip()
                    if title:
                        return title

            subjects = []
            file_elements = dom.getElementsByTagName("file")
            for file_element in file_elements:
                subject = file_element.getAttribute("subject")
                if subject:
                    subjects.append(subject)

            prefixes = []
            for subject in subjects:
                parts = subject.split(" - ")
                if len(parts) >= 2:
                    # Strip any trailing or leading punctuation
                    prefixes.append(parts[0].strip(" -_.[]"))

            if prefixes:
                common_prefix = os.path.commonprefix(prefixes).strip(" -_.[]")
                if common_prefix:
                    return common_prefix

            filenames = []
            for subject in subjects:
                # Filenames are commonly enclosed in quotes inside the subject string
                m = re.search(r'"([^"]+)"', subject)
                if m is not None:
                    filenames.append(m.group(1))

                else:
                    # Fallback: look for a block of text with a file extension
                    m = re.search(r'([\w\-.+\[\]\s]+\.[a-zA-Z0-9]{2,4})\b', subject)
                    if m is not None:
                        filenames.append(m.group(1))

            if filenames:
                base_names = []
                for filename in filenames:
                    # Strip volume suffixes (e.g., .part01.rar, .vol00+01.par2, .r01)
                    name = re.sub(r'\.(?:part\d+\.rar|vol\d+\+\d+\.par2)$', '', filename, re.IGNORECASE)
                    if name == filename:
                        name = os.path.splitext(filename)[0]

                    # Strip any trailing or leading punctuation
                    name = name.strip(' -_.[]')

                    if name:
                        base_names.append(name)

                # Generate the package name by finding the most common base name
                if base_names:
                    common_name = os.path.commonprefix(base_names).strip(" -_.[]")
                    if common_name:
                        return common_name

            return None

        finally:
            dom.unlink()
