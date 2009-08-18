var dwProgressBar = new Class({

	//implements
	Implements: [Options],

	//options
	options: {
		container: $$('body')[0],
		boxID:'',
		percentageID:'',
		displayID:'',
		startPercentage: 0,
		displayText: false,
		speed:10
	},

	//initialization
	initialize: function(options) {
		//set options
		this.setOptions(options);
		//create elements
		this.createElements();
	},

	//creates the box and percentage elements
	createElements: function() {
		var box = new Element('div', { id:this.options.boxID + this.options.id, 'class' : this.options.boxID});
		var perc = new Element('div', { id:this.options.percentageID + this.options.id, 'style':'width:0px;', 'class' : this.options.percentageID });
		perc.inject(box);
		box.inject(this.options.container);
		if(this.options.displayText) {
			var text = new Element('div', { id:this.options.displayID + this.options.id, 'class' : this.options.displayID });
			text.inject(this.options.container);
		}
		this.set(this.options.startPercentage);
	},

	//calculates width in pixels from percentage
	calculate: function(percentage) {
		return (document.id(this.options.boxID+ this.options.id).getStyle('width').replace('px','') * (percentage / 100)).toInt();
	},

	//animates the change in percentage
	animate: function(to) {
		document.id(this.options.percentageID+ this.options.id).set('morph', { duration: this.options.speed, link:'cancel' }).morph({width:this.calculate(to.toInt())});
		if(this.options.displayText) {
			document.id(this.options.displayID+ this.options.id).set('text', to.toInt() + '%');
		}
	},

	//sets the percentage from its current state to desired percentage
	set: function(to) {
		this.animate(to);
	}

});


req = new Request.JSON({
    onSuccess: renderTable,
    method: 'get',
    url: '/json/links',
    initialDelay: 0,
    delay: 1000,
    limit: 20000
});


function renderTable(data){

data.downloads.forEach()

}

window.addEvent('domready', function(){

//create the progress bar for example 1
pb = new dwProgressBar({
        container: $$('.level1 p')[0],
        startPercentage: 25,
        speed: 1000,
        id: 1,
        boxID: 'box',
        percentageID: 'perc',
        displayText: true,
        displayID: 'boxtext'
});

req.startTimer();


 });



