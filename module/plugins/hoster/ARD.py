import subprocess
import re
import os.path
import os

from module.utils import save_join, save_path
from module.plugins.Hoster import Hoster

# Requires rtmpdump
# by Roland Beermann


class RTMP:
    # TODO: Port to some RTMP-library like rtmpy or similar
    # TODO?: Integrate properly into the API of pyLoad

    command = "rtmpdump"

    @classmethod
    def download_rtmp_stream(cls, url, output_file, playpath=None):
        opts = [
            "-r", url,
            "-o", output_file,
        ]
        if playpath:
            opts.append("--playpath")
            opts.append(playpath)

        cls._invoke_rtmpdump(opts)

    @classmethod
    def _invoke_rtmpdump(cls, opts):
        args = [
            cls.command
        ]
        args.extend(opts)

        return subprocess.check_call(args)


class ARD(Hoster):
    __name__ = "ARD Mediathek"
    __version__ = "0.12"
    __pattern__ = r"http://www\.ardmediathek\.de/.*"
    __config__ = []

    def process(self, pyfile):
        site = self.load(pyfile.url)

        avail_videos = re.findall(
            r'mediaCollection.addMediaStream\(0, ([0-9]*), "([^\"]*)", "([^\"]*)", "[^\"]*"\);', site)
        avail_videos.sort(key=lambda videodesc: int(videodesc[0]),
                          reverse=True)  # The higher the number, the better the quality

        quality, url, playpath = avail_videos[0]

        pyfile.name = re.search(r"<h1>([^<]*)</h1>", site).group(1)

        if url.startswith("http"):
            # Best quality is available over HTTP. Very rare.
            self.download(url)
        else:
            pyfile.setStatus("downloading")

            download_folder = self.config['general']['download_folder']

            location = save_join(download_folder, pyfile.package().folder)

            if not os.path.exists(location):
                os.makedirs(location, int(self.config["permission"]["folder"], 8))

                if self.config["permission"]["change_dl"] and os.name != "nt":
                    try:
                        uid = getpwnam(self.config["permission"]["user"])[2]
                        gid = getgrnam(self.config["permission"]["group"])[2]

                        chown(location, uid, gid)
                    except Exception, e:
                        self.logWarning(_("Setting User and Group failed: %s") % str(e))

            output_file = save_join(location, save_path(pyfile.name)) + os.path.splitext(playpath)[1]

            RTMP.download_rtmp_stream(url, playpath=playpath, output_file=output_file)
