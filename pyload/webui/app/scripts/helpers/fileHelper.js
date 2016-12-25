// Helpers to render the file view
define('helpers/fileHelper', ['handlebars', 'utils/apitypes', 'helpers/formatTimeLeft'],
  function(Handlebars, Api, formatTime) {
    'use strict';

    function fileClass(file, options) {
      if (file.finished)
        return 'finished';
      else if (file.failed)
        return 'failed';
      else if (file.offline)
        return 'offline';
      else if (file.online)
        return 'online';
      else if (file.waiting)
        return 'waiting';
      else if (file.downloading)
        return 'downloading';

      return '';
    }

    function fileIcon(media, options) {
      switch (media) {
        case Api.MediaType.Audio:
          return 'icon-music';
        case Api.MediaType.Image:
          return 'icon-picture';
        case Api.MediaType.Video:
          return 'icon-film';
        case Api.MediaType.Document:
          return 'icon-file-text';
        case Api.MediaType.Archive:
          return 'icon-archive';
        case Api.MediaType.Executable:
          return 'icon-cog';
        default:
          return 'icon-file-alt';
      }
    }

    // TODO rest of the states
    function fileStatus(file, options) {
      var s;
      var msg = file.download.statusmsg;

      if (file.failed) {
        s = '<i class="icon-remove"></i>&nbsp;';
        if (file.download.error)
          s += file.download.error;
        else s += msg;
      } else if (file.finished)
        s = '<i class="icon-ok"></i>&nbsp;' + msg;
      else if (file.downloading)
        s = '<div class="progress"><div class="bar" style="width: ' + file.progress + '%">&nbsp;&nbsp;' +
          formatTime(file.eta) + '</div></div>';
      else if (file.waiting)
        s = '<i class="icon-time"></i>&nbsp;' + formatTime(file.eta);
      else
        s = msg;

      return new Handlebars.SafeString(s);
    }

    Handlebars.registerHelper('fileClass', fileClass);
    Handlebars.registerHelper('fileIcon', fileIcon);
    Handlebars.registerHelper('fileStatus', fileStatus);
    return fileClass;
  });
