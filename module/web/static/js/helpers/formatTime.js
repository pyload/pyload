// Format bytes in human readable format
define('helpers/formatTime', ['handlebars'], function(Handlebars) {

    // TODO: seconds are language dependant
    // time could be better formatted
    function seconds2time (seconds) {
        var hours   = Math.floor(seconds / 3600);
        var minutes = Math.floor((seconds - (hours * 3600)) / 60);
        seconds = seconds - (hours * 3600) - (minutes * 60);
        var time = "";

        if (hours != 0) {
            time = hours+":";
        }
        if (minutes != 0 || time !== "") {
            minutes = (minutes < 10 && time !== "") ? "0"+minutes : String(minutes);
            time += minutes+":";
        }
        if (time === "") {
            time = seconds+"s";
        }
        else {
            time += (seconds < 10) ? "0"+seconds : String(seconds);
        }
        return time;
    }


    function formatTime(seconds, options) {
        if (seconds === Infinity)
            return '∞';
        else if (!seconds || seconds <= 0)
            return "-";

        return seconds2time(seconds);
    }

    Handlebars.registerHelper('formatTime', formatTime);
    return formatTime;
});