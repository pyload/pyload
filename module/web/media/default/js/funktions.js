// JavaScript Document
function SecToRightTime(sek)
{
	vreturn = sek > 86400 ? sprintf('%d Tag%s ', sek / 86400, Math.floor(sek / 86400) != 1 ? 'e':'') : '';
	vreturn += sprintf('%02d:%02d:%02d', sek / 3600 % 24, sek / 60 % 60, sek % 60 );
	return vreturn;
}

function HumanFileSize(size)
{
	var filesizename = new Array("KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB");
	var loga = Math.log(size)/Math.log(1024);
	var i = Math.floor(loga);
	var a = Math.pow(1024, i);
	return Math.round( size / a , 2) + " " + filesizename[i];
}

Array.prototype.remove = function(from, to) {
  var rest = this.slice((to || from) + 1 || this.length);
  this.length = from < 0 ? this.length + from : from;
  if (this.length == 0) return [];
  return this.push.apply(this, rest);
};