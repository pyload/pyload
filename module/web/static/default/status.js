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


window.addEvent('domready', function(){

$$('.statusbutton').each(function(item){

 item.hover(function(e){
     this.tween('opacity',1)
 },function(e){
     this.tween('opacity',0.01)
 }
)
})

fx_reveal = new Fx.Reveal($('addlinks'));
//fx_reveal.dissolve()


$$('#addlinks .closeSticky').each(function(el){

el.addEvent('click',function(e){

fx_reveal.dissolve();

});

});

$$('.statusbutton')[2].addEvent('click',function(e){

$('addlinks').setStyle('top', e.page.y + 5)
$('addlinks').setStyle('left', e.page.x + 5)

fx_reveal.reveal()

});

});