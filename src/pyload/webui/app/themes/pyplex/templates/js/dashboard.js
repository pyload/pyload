{% autoescape true %}

$(() => new EntryManager());

const labelColor = (color) => {
  const colorMap = {
    5: 'label-warning',
    7: 'label-info',
    12: 'label-success',
    13: 'label-primary'
  };

  return colorMap[color] || 'label-default';
};

class LinkEntry {
  constructor(id) {
    this.fid = id;
    this.id = id;
  }

  parse() {
    this.elements = {
      tr: $(`#link_${this.id}`),
      name: $(`#link_${this.id}_name`),
      hoster: $(`#link_${this.id}_hoster`),
      status: $(`#link_${this.id}_status`),
      info: $(`#link_${this.id}_info`),
      bleft: $(`#link_${this.id}_bleft`),
      percent: $(`#link_${this.id}_percent`),
      remove: $(`#link_${this.id}_remove`),
      pgbTr: $(`#link_${this.id}_pgb_tr`),
      pgb: $(`#link_${this.id}_pgb`),
    };
    this.initEffects();
  }

  insert(item) {
    try {
      const tr = $('<tr>').css('display', 'none');
      const status = $('<td>').html('&nbsp;').addClass('hidden-xs');
      const statusspan = $('<span>').html(item.statusmsg).addClass(`label ${labelColor(item.status)} lbl_status`);
      const name = $('<td>').html(item.name);
      const hoster = $('<td>').html(item.plugin);
      const info = $('<td>').html(item.info);
      const bleft = $('<td>').html(humanFileSize(item.size)).addClass('hidden-xs');
      const percent = $('<span>').html(`${item.percent}% / ${humanFileSize(item.size - item.bleft)}`).addClass('hidden-xs');
      const remove = $('<span>').addClass('glyphicon glyphicon-remove').css({ 'margin-left': '3px', 'cursor': 'pointer' });
      const pgbTr = $('<tr>').css('border-top-color', '#fff');
      const progress = $('<div>').addClass('progress').css({ 'margin-bottom': '0px', 'margin-left': '4px' });
      const pgb = $('<div>').html(`${item.percent}%`).attr('role', 'progress').addClass('progress-bar progress-bar-striped active').css({ 'height': '35px', 'width': `${item.percent}%` });

      this.elements = {
        tr,
        status,
        statusspan,
        name,
        hoster,
        info,
        bleft,
        percent,
        remove,
        pgbTr,
        progress,
        pgb
      };

      this.elements.status.append(this.elements.statusspan);
      this.elements.progress.append(this.elements.pgb);
      this.elements.tr.append(this.elements.status, this.elements.name, this.elements.hoster, this.elements.info, this.elements.bleft, this.elements.bleft, this.elements.bleft, this.elements.bleft);

      const child = $('<td>').append(this.elements.percent, this.elements.remove);
      this.elements.tr.append(child);

      const secondChild = $('<td>').attr('colspan', 6).append(this.elements.progress);
      this.elements.pgbTr.append(secondChild);

      this.initEffects();
    } catch (e) {
      alert(e);
    }
  }

  initEffects() {
    this.fade = this.elements.tr;
    this.fadeBar = this.elements.pgbTr;

    $(this.elements.remove).click(() => {
      $.get({
        url: "{{url_for('json.abort_link')}}",
        data: { id: this.id },
        traditional: true,
      });
    });
  }

  update(item) {
    $(this.elements.name).text(item.name);
    $(this.elements.hoster).text(item.plugin);
    $(this.elements.statusspan).text(item.statusmsg);
    $(this.elements.info).text(item.info);
    $(this.elements.bleft).text(item.format_size);
    $(this.elements.percent).text(`${item.percent}% / ${humanFileSize(item.size - item.bleft)}`);
    $(this.elements.statusspan).removeClass().addClass(`label ${labelColor(item.status)} lbl_status`);
    $(this.elements.pgb).css('width', `${item.percent}%`).animate({ duration: 'slow' });
    $(this.elements.pgb).html(`${item.percent}%`);
  }

  remove() {
    $(this.fade).fadeOut("slow", function() {
      this.remove();
    });
    $(this.fadeBar).fadeOut("slow", function() {
      this.remove();
    });
  }
}

class EntryManager {
  constructor() {
    this.entries = new Map();
    this.container = $('#links_active');
    this.fetchInterval = null;
    this.initialize();
  }

  initialize() {
    this.fetchLinks();
    this.fetchInterval = setInterval(() => this.fetchLinks(), 2500);
    {% for link in content %}
    this.entries.set({{link.id}}, new LinkEntry({{link.id}}));
    {% endfor %}
    this.parseFromContent();
  }

fetchLinks() {
  $.ajax({
    method: "post",
    url: "{{url_for('json.links')}}",
    async: true,
    timeout: 30000,
    success: (data) => this.update(data),
    error: (xhr) => {
      if (xhr.status === 400) {
        if (this.fetchInterval) {
          clearInterval(this.fetchInterval);
          this.fetchInterval = null;
          uiHandler.indicateInfo("{{_('Status updates stopped due to authentication error,<br>please refresh the page')}}", 0);
        }
      }
      this.update({ ids: [], links: [] });
    }
  });
}

  parseFromContent() {
    this.entries.forEach((entry, id) => {
      entry.parse();
    });
  }

  update(data) {
    try {
      const dataIds = new Set(data.links.map(item => item.fid));
      const removedIds = [...this.entries.keys()].filter(id => !dataIds.has(id));

      removedIds.forEach(entryId => {
        const entry = this.entries.get(entryId);
        if (entry) {
          entry.remove();
          this.entries.delete(entryId);
        }
      });

      data.links.forEach(link => {
        if (this.entries.has(link.fid)) {
          const entry = this.entries.get(link.fid);
          if (entry) {
            entry.update(link);
          }
        } else {
          const entry = new LinkEntry(link.fid);
          entry.insert(link);
          this.entries.set(link.fid, entry);
          this.container.append(entry.elements.tr);
          this.container.append(entry.elements.pgbTr);
          $(entry.fade).fadeIn('fast');
          $(entry.fadeBar).fadeIn('fast');
        }
      });
    } catch (e) {
      alert(e);
    }
  }
}

{% endautoescape %}
