# External scope
root = this

# Provided we have the right hooks, following notifications might be useful:
#  * CAPTCHA is pending    (Minimal sample implementation as shown below)
#  * Reconnecting..        (Will require a delay before reconnect, so Web-UI can fetch this information)
#  * Reconnect successful  (Simple information about IP change)
#  * Package finished      (Including extraction, so ready to use)
#  * Queue finished        (Python goes to IDLE mode)
#  * Links collected       (Confirmation that click'n'load was successful)
# Not implemented:
#  * Package failed        (Either immediately or when pyload can't do any more actions with this package, so user can help to restart or solve)
#  * File finished
#  * File failed
#
# I would divide the above in two groups:
#  * (ongoing) notifications
#  * informations
#
# Notifications
#  There is an event that requires immediate user interaction. The notification will disappear, when user interaction is no more required.
#  (CAPTCHAS)
#
# Informations
#  Informations are short notices, that will disappear after a certain (configureable) timeout
#  (All other)
#
#
# Some notifications could be derived from current XHR request as "CAPTCHA" or "Queue".
# Others would need an extension of the JSON API
#  * To be added to "https://github.com/pyload/pyload/blob/stable/module/Api.py :: statusServer"
#
#
# IDEA:
#  A boolean flag for new events is not enough if more than one client is connected, as wen do not know when to reset the flag.
#  Better: Timestap of the last occurence for an event of a certain time.
#          Then, every client can check for itself if the timestamp changed since last status request.
#
# TODO before integration:
# * Discuss placement of notification configuration
# * Discuss selection of text bits. Maybe there are translated text bits that fit the purpose
# * Discuss selection of Notification logo
# * Discuss default settings

# Notification availability and permissions of web browser
NotificationAvailable = false
if "{{notifications.activated.value}}".toLowerCase() is "true" # Checking Config[webinterfaceNotifications].activated
    if Notification?
        Notification.requestPermission() if Notification.permission is "default"
        NotificationAvailable = true if Notification.permission is "granted"

NotificationFirstRequest = true

# Data for each notification type
#  ongoing: Notification is currently visible
#  object:  Variable of created Notification
#  last:    Timestamp of last event. Used for detection of new events
#  timer:   TimerID returned by setTimeout
#  tag:     For Notification sharing the same tag only the latest will be shown
#  message: Notification text
#  clickEvent:  Action to be executed when clicking on the notification
#  closeEvent:  Action to be executed when clicking the 'x' of the notification
#  enabled: Notification is activated and will be shown
class pyNotify
    constructor: ({tag, message, timeout, clickEvent, closeEvent} = {}) ->
        @ongoing = false
        @object = null
        @last = 0
        @timer = null
        @tag = tag ? ''
        @message = message
        @timeout = parseInt timeout
        @timeout = 5 if isNaN @timeout
        @timeout *= 1000                    #Timeout needs to be converted into milliseconds
        @clickEvent = clickEvent ? null
        @closeEvent = closeEvent ? null

        @enabled = if @timeout < 0 then false else true  #Negative values disable the notification

    CreateNotification: ->
        if @timeout < 0
            return
        if @timer
            clearTimeout @timer
            @timer = null
        @object = new Notification('pyLoad', {
            icon: '/media/plugins/WebinterfaceNotify/WebinterfaceNotifyLogo_static.png',
            body: @message
            tag:  @tag
        } )
        @object.addEventListener 'click', @clickEvent if @clickEvent?
        @object.addEventListener 'close', @closeEvent if @closeEvent?
        @ongoing = true
        #Using third parameter of setTimeout to pass context to called function as parameter
        @timer = setTimeout ((me)-> me.DestroyNotification()), @timeout, this if @timeout > 0
        return

    DestroyNotification: ->
        @object.close()
        @object = null
        @ongoing = false
        @timer = null
        return

NotificationData = {
    captcha: new pyNotify
        tag:'captcha',
        message:'{{_("Captcha waiting")}}',
        clickEvent: (->$("cap_info").click()),
        timeout: '{{notifications.timeCaptcha.value}}'
    reconnecting: new pyNotify
        tag:'reconnect',
        message:'{{_("Reconnecting...")}}',
        timeout: '{{notifications.timeReconnecting.value}}'
    reconnectFinished: new pyNotify
        tag:'reconnect',
        message:'{{_("Reconnect complete!")}}',
        timeout: '{{notifications.timeReconnectFinished.value}}'
    fileFinished: new pyNotify
        tag:'file',
        message:'{{_("File finished!")}}',
        timeout: '{{notifications.timeFileFinished.value}}'
    fileFailed: new pyNotify
        tag:'file',
        message:'{{_("File failed!")}}',
        timeout: '{{notifications.timeFileFailed.value}}'
    packageFinished: new pyNotify
        tag:'package',
        message:'{{_("Package finished!")}}',
        timeout: '{{notifications.timePackageFinished.value}}'
#    packageFailed: new pyNotify
#        tag:'package',
#        message:'{{_("Package failed!")}}',
#        timeout: '{{notifications.timePackageFailed.value}}'
    queueFinished: new pyNotify
        tag:'queue',
        message:'{{_("Queue finished!")}}',
        timeout: '{{notifications.timeQueueFinished.value}}'
    queueFailed: new pyNotify
        tag:'queue',
        message:'{{_("Queue failed!")}}',
        timeout: '{{notifications.timeQueueFinished.value}}'
#    linksCollected: new pyNotify
#        tag:'links',
#        message:'{{_("New links added")}}',
#        timeout: '{{notifications.timeLinksCollected.value}}'
    pluginsUpdated: new pyNotify
        tag:'plugins',
        message:'{{_("Plugins updated!")}}',
        timeout: '{{notifications.timePluginsUpdated.value}}'
}

# helper functions


document.addEvent "domready", ->

    new Request.JSON({
        url: '/api/call?info='+encodeURIComponent('{"plugin":"WebinterfaceNotify","func":"get_timestamps","arguments":None,"parseArguments":None}')
        onSuccess: NotifyLoadJsonToContent
        secure: false
        async: true
        initialDelay: 0
        delay: 4000
        limit: 3000
    }).startTimer()

NotifyLoadJsonToContent = (data) ->
    
    # variable data is double-stringified as it is served via "RPC" API-call
    data = JSON.parse(data)
    if NotificationAvailable
        for event, time of data
            nData = NotificationData[event]
            if nData? and nData.last < time
                nData.last = time
                if not NotificationFirstRequest     #Take the first request after page load to initialise the local variables
                    nData.CreateNotification() if nData.enabled and not nData.ongoing
            if nData? and time is 0
                nData.last = time
                nData.DestroyNotification() if nData.ongoing
                
    NotificationFirstRequest = false
    return null

