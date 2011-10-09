# External scope
root = this

# helper functions
humanFileSize = (size) ->
    filesizename = new Array("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    loga = Math.log(size) / Math.log(1024)
    i = Math.floor(loga)
    a = Math.pow(1024, i)
    if size is 0 then "0 B" else (Math.round(size * 100 / a) / 100 + " " + filesizename[i])

parseUri = () ->
    oldString = $("add_links").value
    regxp = new RegExp('(ht|f)tp(s?):\/\/[a-zA-Z0-9\-\.\/\?=_&%#]+[<| |\"|\'|\r|\n|\t]{1}', 'g')
    resu = oldString.match regxp
    return if resu == null
    res = "";

    for part in resu
        if part.indexOf(" ") != -1
            res = res + part.replace(" ", " \n")
        else if part.indexOf("\t") != -1
            res = res + part.replace("\t", " \n")
        else if part.indexOf("\r") != -1
            res = res + part.replace("\r", " \n")
        else if part.indexOf("\"") != -1
            res = res + part.replace("\"", " \n")
        else if part.indexOf("<") != -1
            res = res + part.replace("<", " \n")
        else if part.indexOf("'") != -1
            res = res + part.replace("'", " \n")
        else
            res = res + part.replace("\n", " \n")

    $("add_links").value = res;


Array::remove = (from, to) ->
    rest = this.slice((to || from) + 1 || this.length)
    this.length = from < 0 ? this.length + from : from
    return [] if this.length == 0
    return this.push.apply(this, rest)


document.addEvent "domready", ->

    # global notification
    root.notify = new Purr {
        'mode': 'top'
        'position': 'center'
    }

    root.captchaBox = new MooDialog {destroyOnHide: false}
    root.captchaBox.setContent $ 'cap_box'

    root.addBox = new MooDialog {destroyOnHide: false}
    root.addBox.setContent $ 'add_box'

    $('add_form').onsubmit = ->
        $('add_form').target = 'upload_target'
        if $('add_name').value is "" and $('add_file').value is ""
            alert '{{_("Please Enter a packagename.")}}'
            return false
        else
            root.addBox.close()
            return true

    $('add_reset').addEvent 'click', -> root.addBox.close()

    $('action_add').addEvent 'click', -> $("add_form").reset(); root.addBox.open()
    $('action_play').addEvent 'click', -> new Request({method: 'get', url: '/api/unpauseServer'}).send()
    $('action_cancel').addEvent 'click', -> new Request({method: 'get', url: '/api/stopAllDownloads'}).send()
    $('action_stop').addEvent 'click', -> new Request({method: 'get', url: '/api/pauseServer'}).send()


    # captcha events

    $('cap_info').addEvent 'click', ->
        load_captcha "get", ""
        root.captchaBox.open()
    $('cap_reset').addEvent 'click', -> root.captchaBox.close()
    $('cap_form').addEvent 'submit', (e) ->
        submit_captcha()
        e.stop()

    $('cap_positional').addEvent 'click', on_captcha_click

    new Request.JSON({
        url: "/json/status"
        onSuccess: LoadJsonToContent
        secure: false
        async: true
        initialDelay: 0
        delay: 4000
        limit: 3000
    }).startTimer()

LoadJsonToContent = (data) ->
    $("speed").set 'text', humanFileSize(data.speed)+"/s"
    $("aktiv").set 'text', data.active
    $("aktiv_from").set 'text', data.queue
    $("aktiv_total").set 'text', data.total

    if data.captcha
        if $("cap_info").getStyle("display") != "inline"
            $("cap_info").setStyle 'display', 'inline'
            root.notify.alert '{{_("New Captcha Request")}}', {
                            'className': 'notify'
                        }
    else
        $("cap_info").setStyle 'display', 'none'


    if data.download
        $("time").set 'text', ' {{_("on")}}'
        $("time").setStyle 'background-color', "#8ffc25"
    else
        $("time").set 'text', ' {{_("off")}}'
        $("time").setStyle 'background-color', "#fc6e26"

    if data.reconnect
        $("reconnect").set 'text', ' {{_("on")}}'
        $("reconnect").setStyle 'background-color', "#8ffc25"
    else
        $("reconnect").set 'text', ' {{_("off")}}'
        $("reconnect").setStyle 'background-color', "#fc6e26"

    return null


set_captcha = (data) ->
    $('cap_id').set 'value', data.id
    if (data.result_type is 'textual')
        $('cap_textual_img').set 'src', data.src
        $('cap_title').set 'text', '{{_("Please read the text on the captcha.")}}'
        $('cap_submit').setStyle 'display', 'inline'
        $('cap_textual').setStyle 'display', 'block'
        $('cap_positional').setStyle 'display', 'none'

    else if (data.result_type == 'positional')
        $('cap_positional_img').set('src', data.src)
        $('cap_title').set('text', '{{_("Please click on the right captcha position.")}}')
        $('cap_submit').setStyle('display', 'none')
        $('cap_textual').setStyle('display', 'none')


load_captcha = (method, post) ->
    new Request.JSON({
        url: "/json/set_captcha"
        onSuccess: (data) -> set_captcha(data) if data.captcha else clear_captcha()
        secure: false
        async: true
        method: method
    }).send(post)

clear_captcha = ->
    $('cap_textual').setStyle 'display', 'none'
    $('cap_textual_img').set 'src', ''
    $('cap_positional').setStyle 'display', 'none'
    $('cap_positional_img').set 'src', ''
    $('cap_title').set 'text', '{{_("No Captchas to read.")}}'

submit_captcha = ->
    load_captcha("post", "cap_id=" + $('cap_id').get('value') + "&cap_result=" + $('cap_result').get('value') );
    $('cap_result').set('value', '')
    false

on_captcha_click = (e) -> 
    position = e.target.getPosition()
    x = e.page.x - position.x
    y = e.page.y - position.y
    $('cap_result').value = x + "," + y
    submit_captcha()