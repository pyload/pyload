{% autoescape true %}

var em;

$( document ).ready(function() {
    em = new EntryManager();
});

function labelcolor(color)
{
    if (color === 5) {
            return 'label-warning';
    } else if (color === 7) {
            return 'label-info';
    } else if (color === 12) {
            return 'label-success';
    } else if (color === 13) {
            return 'label-primary';
    } else {
            return 'label-default';
    }
}

function EntryManager(){
    var ids;
    var entries=[];
    var container;
    this.initialize = function() {
        thisObject=this;
        $.ajax({
            method:"post",
            url: "{{url_for('json.links')}}",
            async: true,
            timeout: 30000,
            success: thisObject.update
        });
        setInterval(function() {
        $.ajax({
            method:"post",
            url: "{{url_for('json.links')}}",
            async: true,
            timeout: 30000,
            success: thisObject.update,
            error: function () {
                thisObject.update({ids:[], links:[]})
            }
        });
    }, 2500);

        ids = [{% for link in content %}
        {% if forloop.last %}
            {{link.id}}
        {% else %}
         {{link.id}},
        {% endif %}
        {% endfor %}];

        container = $('#links_active');

        this.parseFromContent();

        // this.json.startTimer();
    };
    this.parseFromContent = function (){
        $.each(ids,function(id,index){
            var entry = new LinkEntry(id);
            entry.parse();
            entries.push(entry)
        });
    };
    this.update = function (data){
        try{
            ids = entries.map(function(item){
                return item.fid;
            });
            const dataids = data.links.map(function (item) {
                return item.fid;
            });
            var temp=ids.filter(function(id){
                return $.inArray(id, dataids) <= -1;
            },dataids);
            $.each(temp,function(id){
                var elementid=Number(String(this));
                var index = ids.indexOf(elementid);
                entries[index].remove();
                entries = entries.filter(function(item){return item.fid !== elementid},id);
                ids.splice( $.inArray(elementid, ids), 1 );
                //ids.splice(index,1);
                // ids = ids.erase(id);
             });

            $.each(data.links,function(i,link){
                var index= $.inArray(link.fid,ids);
                if (index > -1){
                    entries[index].update(link);
                }else{
                    var entry = new LinkEntry(link.fid);
                    entry.insert(link);
                    entries.push(entry);
                    ids.push(link.fid);
                    container[0].appendChild(entry.elements.tr);
                    container[0].appendChild(entry.elements.pgbTr);
                    $(entry.fade).fadeIn('fast');
                    $(entry.fadeBar).fadeIn('fast');

                }
            });
        }catch(e){
            alert(e)
        }
    };
    // initialize object
    this.initialize();
}


function LinkEntry(id){

    this.initialize = function(id){
        this.fid = id;
        this.id = id;
    };

    this.parse = function(){
        this.elements = {
            tr: $("#link_"+this.id),
            name: $("#link_"+this.id+"_name"),
            hoster:$("#link_"+this.id+"_hoster"),
            status: $("#link_"+this.id+"_status"),
            info: $("#link_"+this.id+"_info"),
            bleft: $("#link_"+this.id+"_bleft"),
            percent: $("#link_"+this.id+"_percent"),
            remove: $("#link_"+this.id+"_remove"),
            pgbTr: $("#link_"+this.id+"_pgb_tr"),
            pgb: $("#link_"+this.id+"_pgb"),
        };
        this.initEffects();
    };
    this.insert = function(item){
        try{
            var tr = document.createElement("tr");
            $(tr).html('');
            $(tr).css('display','none')
            var status = document.createElement("td");
            $(status).html('&nbsp;');
            $(status).addClass('hidden-xs');
            var statusspan = document.createElement("span");
            $(statusspan).html(item.statusmsg);
            $(statusspan).removeClass().addClass('label '+ labelcolor(item.status) + ' lbl_status');
            var name = document.createElement("td");
            $(name).html(item.name);
            var hoster = document.createElement("td");
            $(hoster).html(item.plugin);
            var info = document.createElement("td");
            $(info).html(item.info);
            var bleft = document.createElement("td");
            $(bleft).html(humanFileSize(item.size));
            $(bleft).addClass('hidden-xs');
            var percent = document.createElement("span");
            $(percent).html(item.percent+ '% / '+ humanFileSize(item.size-item.bleft));
            $(percent).addClass('hidden-xs');
            var remove= document.createElement("span");
            $(remove).html('');
            $(remove).addClass('glyphicon glyphicon-remove');
            $(remove).css('margin-left','3px');
            $(remove).css('cursor','pointer');
            var pgbTr= document.createElement("tr");
            $(pgbTr).html('');
            $(pgbTr).css('border-top-color','#fff');
            var progress= document.createElement("div");
            $(progress).html('');
            $(progress).addClass('progress');
            $(progress).css('margin-bottom','0px');
            $(progress).css('margin-left', '4px');
            //$(progress).addClass('progress-bar progress-bar-striped active');
            //$(progress).data('role', 'progressbar');
            //$(progress).data('aria-valuenow', '0');
            //$(progress).data('aria-valuemin', '0');
            //$(progress).data('aria-valuemax', '100');
            //$(progress).css('margin-bottom','0px');
            var pgb= document.createElement("div");
            $(pgb).html('' + item.percent + '%');
            $(pgb).attr('role','progress');
            $(pgb).addClass('progress-bar progress-bar-striped active');
            $(pgb).data('role', 'progressbar');
            $(pgb).data('aria-valuenow', '0');
            $(pgb).data('aria-valuemin', '0');
            $(pgb).data('aria-valuemax', '100');
            $(pgb).css('height', '35px');
            $(pgb).css('width',item.percent+'%');

        this.elements = {
            tr:tr,
            status:status,
            statusspan:statusspan,
            name:name,
            hoster:hoster,
            info:info,
            bleft:bleft,
            percent:percent,
            remove:remove,
            pgbTr:pgbTr,
            progress:progress,
            pgb:pgb
        };


        this.elements.status.appendChild(this.elements.statusspan);
        this.elements.progress.appendChild(this.elements.pgb);
        this.elements.tr.appendChild(this.elements.status);
        this.elements.tr.appendChild(this.elements.name);
        this.elements.tr.appendChild(this.elements.hoster);
        this.elements.tr.appendChild(this.elements.info);
        this.elements.tr.appendChild(this.elements.bleft);
        this.elements.tr.appendChild(this.elements.bleft);
        this.elements.tr.appendChild(this.elements.bleft);
        this.elements.tr.appendChild(this.elements.bleft);

        var child = document.createElement('td');
        child.appendChild(this.elements.percent);
        child.appendChild(this.elements.remove);

        this.elements.tr.appendChild(child);

        var secondchild = document.createElement('td');
        $(secondchild).attr('colspan',6);
        secondchild.appendChild(this.elements.progress);

        this.elements.pgbTr.appendChild(secondchild);

        this.initEffects();
        }catch(e){
            alert(e);
        }
    };

    this.initEffects = function(){
        //if(!operafix)
            // this.bar = new Fx.Morph(elements.pgb, {unit: '%', duration: 5000, link: 'link', fps:30});
        // ToDo Fix
        this.fade = this.elements.tr;
        this.fadeBar = this.elements.pgbTr;

        $(this.elements.remove).click(function(){
            $.get({
                url: "{{url_for('json.abort_link')}}",
                data: {id: id},
                traditional: true,
            })
        })
    };
    this.update = function(item){
            $(this.elements.name).text(item.name);
            $(this.elements.hoster).text(item.plugin);
            $(this.elements.statusspan).text(item.statusmsg);
            $(this.elements.info).text(item.info);
            $(this.elements.bleft).text(item.format_size);
            $(this.elements.percent).text(item.percent+ '% / '+ humanFileSize(item.size-item.bleft));
            $(this.elements.statusspan).removeClass().addClass('label '+labelcolor(item.status) + ' lbl_status');
            $(this.elements.pgb).css('width',item.percent+'%').animate({duration:'slow'});
            $(this.elements.pgb).html('' + item.percent + '%');

    };
    this.remove = function(){
        $(this.fade).fadeOut("slow",function(){
            this.remove();
        });
        $(this.fadeBar).fadeOut("slow",function(){
            this.remove();
        });
    };
    this.initialize(id);
}

{% endautoescape %}
