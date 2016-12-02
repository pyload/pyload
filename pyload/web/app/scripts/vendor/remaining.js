/**
 * Javascript Countdown
 * Copyright (c) 2009 Markus Hedlund
 * Version 1.1
 * Licensed under MIT license
 * http://www.opensource.org/licenses/mit-license.php
 * http://labs.mimmin.com/countdown
 */
define([], function() {
    var remaining = {
        /**
         * Get the difference of the passed date, and now. The different formats of the taget parameter are:
         * January 12, 2009 15:14:00     (Month dd, yyyy hh:mm:ss)
         * January 12, 2009              (Month dd, yyyy)
         * 09,00,12,15,14,00             (yy,mm,dd,hh,mm,ss) Months range from 0-11, not 1-12.
         * 09,00,12                      (yy,mm,dd)          Months range from 0-11, not 1-12.
         * 500                           (milliseconds)
         * 2009-01-12 15:14:00           (yyyy-mm-dd hh-mm-ss)
         * 2009-01-12 15:14              (yyyy-mm-dd hh-mm)
         * @param target Target date. Can be either a date object or a string (formated like '24 December, 2010 15:00:00')
         * @return Difference in seconds
         */
        getSeconds: function(target) {
            var today = new Date();

            if (typeof(target) == 'object') {
                var targetDate = target;
            } else {
                var matches = target.match(/(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})(:(\d{2}))?/);   // YYYY-MM-DD HH-MM-SS
                if (matches != null) {
                    matches[7] = typeof(matches[7]) == 'undefined' ? '00' : matches[7];
                    var targetDate = new Date(matches[1], matches[2] - 1, matches[3], matches[4], matches[5], matches[7]);
                } else {
                    var targetDate = new Date(target);
                }
            }

            return Math.floor((targetDate.getTime() - today.getTime()) / 1000);
        },

        /**
         * @param seconds Difference in seconds
         * @param i18n A language object (see code)
         * @param onlyLargestUnit Return only the largest unit (see documentation)
         * @param hideEmpty Hide empty units (see documentation)
         * @return String formated something like '1 week, 1 hours, 1 second'
         */
        getString: function(seconds, i18n, onlyLargestUnit, hideEmpty) {
            if (seconds < 1) {
                return '';
            }

            if (typeof(hideEmpty) == 'undefined' || hideEmpty == null) {
                hideEmpty = true;
            }
            if (typeof(onlyLargestUnit) == 'undefined' || onlyLargestUnit == null) {
                onlyLargestUnit = false;
            }
            if (typeof(i18n) == 'undefined' || i18n == null) {
                i18n = {
                    weeks: ['week', 'weeks'],
                    days: ['day', 'days'],
                    hours: ['hour', 'hours'],
                    minutes: ['minute', 'minutes'],
                    seconds: ['second', 'seconds']
                };
            }

            var units = {
                weeks: 7 * 24 * 60 * 60,
                days: 24 * 60 * 60,
                hours: 60 * 60,
                minutes: 60,
                seconds: 1
            };

            var returnArray = [];
            var value;
            for (unit in units) {
                value = units[unit];
                if (seconds / value >= 1 || unit == 'seconds' || !hideEmpty) {
                    secondsConverted = Math.floor(seconds / value);
                    var i18nUnit = i18n[unit][secondsConverted == 1 ? 0 : 1];
                    returnArray.push(secondsConverted + ' ' + i18nUnit);
                    seconds -= secondsConverted * value;

                    if (onlyLargestUnit) {
                        break;
                    }
                }
            }
            ;

            return returnArray.join(', ');
        },

        /**
         * @param seconds Difference in seconds
         * @return String formated something like '169:00:01'
         */
        getStringDigital: function(seconds) {
            if (seconds < 1) {
                return '';
            }

            remainingTime = remaining.getArray(seconds);

            for (index in remainingTime) {
                remainingTime[index] = remaining.padNumber(remainingTime[index]);
            }
            ;

            return remainingTime.join(':');
        },

        /**
         * @param seconds Difference in seconds
         * @return Array with hours, minutes and seconds
         */
        getArray: function(seconds) {
            if (seconds < 1) {
                return [];
            }

            var units = [60 * 60, 60, 1];

            var returnArray = [];
            var value;
            for (index in units) {
                value = units[index];
                secondsConverted = Math.floor(seconds / value);
                returnArray.push(secondsConverted);
                seconds -= secondsConverted * value;
            }
            ;

            return returnArray;
        },

        /**
         * @param number An integer
         * @return Integer padded with a 0 if necessary
         */
        padNumber: function(number) {
            return (number >= 0 && number < 10) ? '0' + number : number;
        }
    };
    return remaining;
});
