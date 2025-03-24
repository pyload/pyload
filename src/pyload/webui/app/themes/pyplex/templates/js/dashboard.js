{% autoescape true %}

$(() => new EntryManager());

const labelcolor = (color) => {
  switch (color) {
    case 5:
      return 'label-warning';
    case 7:
      return 'label-info';
    case 12:
      return 'label-success';
    case 13:
      return 'label-primary';
    default:
      return 'label-default';
  }
};

class EntryManager {
  constructor() {
    this.ids = [];
    this.entries = [];
    this.container = $('#links_active');
    this.initialize();
  }

  initialize() {
    this.fetchLinks();
    setInterval(() => this.fetchLinks(), 2500);
    this.ids = [{% for link in content %}
    {{link.id}}{% if not forloop.last %},{% endif %}
    {% endfor %}];
    this.parseFromContent();
  }

  fetchLinks() {
    $.ajax({
      method: "post",
      url: "{{url_for('json.links')}}",
      async: true,
      timeout: 30000,
      success: (data) => this.update(data),
      error: () => this.update({ ids: [], links: [] })
    });
  }

  parseFromContent() {
    this.ids.forEach(id => {
      const entry = new LinkEntry(id);
      entry.parse();
      this.entries.push(entry);
    });
  }

  update(data) {
    try {
      const ids = this.entries.map(item => item.fid);
      const dataids = data.links.map(item => item.fid);
      const temp = ids.filter(id => !dataids.includes(id));

      temp.forEach(elementid => {
        const index = ids.indexOf(elementid);
        this.entries[index].remove();
        this.entries = this.entries.filter(item => item.fid !== elementid);
        this.ids.splice(this.ids.indexOf(elementid), 1);
      });

      data.links.forEach(link => {
        const index = this.ids.indexOf(link.fid);
        if (index > -1) {
          this.entries[index].update(link);
        } else {
          const entry = new LinkEntry(link.fid);
          entry.insert(link);
          this.entries.push(entry);
          this.ids.push(link.fid);
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
      const statusspan = $('<span>').html(item.statusmsg).addClass(`label ${labelcolor(item.status)} lbl_status`);
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

      const secondchild = $('<td>').attr('colspan', 6).append(this.elements.progress);
      this.elements.pgbTr.append(secondchild);

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
    $(this.elements.statusspan).removeClass().addClass(`label ${labelcolor(item.status)} lbl_status`);
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

{% endautoescape %}
