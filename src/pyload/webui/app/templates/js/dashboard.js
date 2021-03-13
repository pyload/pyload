{% autoescape true %}

var em;
var operafix = (navigator.userAgent.toLowerCase().search("opera") >= 0);

document.addEvent("domready", function(){
    em = new EntryManager();
});

var EntryManager = new Class({
    initialize: function(){
        this.json = new Request.JSON({
            url: "{{url_for('json.links')}}",
            secure: false,
            async: true,
            onSuccess: this.update.bind(this),
            initialDelay: 0,
            delay: 2500,
            limit: 30000
        });

        this.ids = [{% for link in content %}
        {% if forloop.last %}
            {{ link.id }}
        {% else %}
         {{ link.id }},
        {% endif %}
        {% endfor %}];

        this.entries = [];
        this.container = $('LinksAktiv');

        this.parseFromContent();

        this.json.startTimer();
    },
    parseFromContent: function(){
        this.ids.each(function(id,index){
            var entry = new LinkEntry(id);
            entry.parse();
            this.entries.push(entry)
            }, this);
    },
    update: function(data){

        try{
        this.ids = this.entries.map(function(item){
            return item.fid
            });

        this.ids.filter(function(id){
            return !this.ids.contains(id)
        },data).each(function(id){
            var index = this.ids.indexOf(id);
            this.entries[index].remove();
            this.entries = this.entries.filter(function(item){return item.fid != this},id);
            this.ids = this.ids.erase(id)
            }, this);

        data.links.each(function(link, i){
            if (this.ids.contains(link.fid)){

                var index = this.ids.indexOf(link.fid);
                this.entries[index].update(link)

            }else{
                var entry = new LinkEntry(link.fid);
                entry.insert(link);
                this.entries.push(entry);
                this.ids.push(link.fid);
                this.container.adopt(entry.elements.tr,entry.elements.pgbTr);
                entry.fade.start('opacity', 1);
                entry.fadeBar.start('opacity', 1);

            }
            }, this)
        }catch(e){
            //alert(e)
        }
    }
});


var LinkEntry = new Class({
    initialize: function(id){
        this.fid = id;
        this.id = id;
    },
    parse: function(){
        this.elements = {
            tr: $("link_{id}".substitute({id: this.id})),
            name: $("link_{id}_name".substitute({id: this.id})),
            status: $("link_{id}_status".substitute({id: this.id})),
            info: $("link_{id}_info".substitute({id: this.id})),
            bleft: $("link_{id}_bleft".substitute({id: this.id})),
            percent: $("link_{id}_percent".substitute({id: this.id})),
            remove: $("link_{id}_remove".substitute({id: this.id})),
            pgbTr: $("link_{id}_pgb_tr".substitute({id: this.id})),
            pgb: $("link_{id}_pgb".substitute({id: this.id}))
        };
        this.initEffects();
    },
    insert: function(item){
        try{

        this.elements = {
            tr: new Element('tr', {
            'html': '',
            'styles':{
                'opacity': 0
            }
            }),
            name: new Element('td', {
            'html': item.name
            }),
            status: new Element('td', {
            'html': item.statusmsg
            }),
            info: new Element('td', {
            'html': item.info
            }),
            bleft: new Element('td', {
            'html': humanFileSize(item.size)
            }),
            percent: new Element('span', {
            'html': item.percent+ '% / '+ humanFileSize(item.size-item.bleft)
            }),
            remove: new Element('img',{
            'src': "{{ url_for('static', filename='img/control-cancel.png') }}",
            'styles':{
                'vertical-align': 'middle',
                'margin-right': '-20px',
                'margin-left': '5px',
                'margin-top': '-2px',
                'cursor': 'pointer'
            }
            }),
            pgbTr: new Element('tr', {
            'html':''
            }),
            pgb: new Element('div', {
            'html': '&nbsp;',
            'styles':{
                'height': '4px',
                'width': item.percent+'%',
                'background-color': '#ddd'
            }
            })
        };

        this.elements.tr.adopt(this.elements.name,this.elements.status,this.elements.info,this.elements.bleft,new Element('td').adopt(this.elements.percent,this.elements.remove));
        this.elements.pgbTr.adopt(new Element('td',{'colspan':5}).adopt(this.elements.pgb));
        this.initEffects();
        }catch(e){
            alert(e)
        }
    },
    initEffects: function(){
        if(!operafix)
            this.bar = new Fx.Morph(this.elements.pgb, {unit: '%', duration: 5000, link: 'link', fps:30});
        this.fade = new Fx.Tween(this.elements.tr);
        this.fadeBar = new Fx.Tween(this.elements.pgbTr);

        this.elements.remove.addEvent('click', function(){
            new Request({
                method: 'get',
                url: "{{url_for('json.abort_link')}}",
                data: {id: this.id}
            }).send();
        }.bind(this));

    },
    update: function(item){
            this.elements.name.set('text', item.name);
            this.elements.status.set('text', item.statusmsg);
            this.elements.info.set('text', item.info);
            this.elements.bleft.set('text', item.format_size);
            this.elements.percent.set('text', item.percent+ '% / '+ humanFileSize(item.size-item.bleft));
            if(!operafix)
            {
                this.bar.start({
                    'width': item.percent,
                    'background-color': [Math.round(120/100*item.percent),100,100].hsbToRgb().rgbToHex()
                });
            }
            else
            {
                this.elements.pgb.set(
                    'styles', {
                        'height': '4px',
                        'width': item.percent+'%',
                        'background-color': [Math.round(120/100*item.percent),100,100].hsbToRgb().rgbToHex(),
                     });
            }
    },
    remove: function(){
            this.fade.start('opacity',0).chain(function(){this.elements.tr.dispose();}.bind(this));
            this.fadeBar.start('opacity',0).chain(function(){this.elements.pgbTr.dispose();}.bind(this));

    }
});

{% endautoescape %}
