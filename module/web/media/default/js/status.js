/* hover! */
Element.implement({
    'hover': function(fn1,fn2) {
        return this.addEvents({
            'mouseenter': function(e) {
                fn1.attempt(e,this);
            },
            'mouseleave': function(e) {
                fn2.attempt(e,this);
            }
        })
    }
});

function updateStatus(data){

    alert("test");
    document.id("status").textContent = "Status: "+ data.status;
    document.id("speed").textContent = "Speed: "+ data.speed +" kb/s";
    document.id("queue").textContent = "Files in queue: "+ data.queue;

}


status_req = new Request.JSON({
    onSuccess: updateStatus,
    method: 'get',
    url: '/json/status',
    initialDelay: 0,
    delay: 2000,
    limit: 20000
});

window.addEvent('domready', function(){

    status_req.startTimer();


    document.id("btAdd").addEvent("click", function(e){

        new Request({
            method: 'post',
            url: '/json/addpackage',
            onSuccess: function(){
                document.id('linkarea').value = ""
            }
            }).send('links='+document.id('linkarea').value+"&name="+document.id('pname').value)


    });

    $$('.statusbutton').each(function(item){

        item.hover(function(e){
            this.tween('opacity',1)
        },function(e){
            this.tween('opacity',0.01)
        }
        )
    });

    fx_reveal = new Fx.Reveal($('addlinks'));
    //fx_reveal.dissolve()


    $$('#addlinks .closeSticky').each(function(el){

        el.addEvent('click',function(e){

            fx_reveal.dissolve();

        });

    });

    $$('.statusbutton')[2].addEvent('click',function(e){

        $('addlinks').setStyle('top', e.page.y + 5);
        $('addlinks').setStyle('left', e.page.x + 5);

        fx_reveal.reveal()

    });

    $$('.statusbutton')[0].addEvent('click', function(e){

        new Request({
            'url' : '/json/play',
            'method' : 'get'
        }).send()
    });

    $$('.statusbutton')[1].addEvent('click', function(e){

        new Request({
            'url' : '/json/pause',
            'method' : 'get'
        }).send()
    })

});