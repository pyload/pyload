    #############################
    ### pyLoad Script Support ###
    #############################

pyLoad is able to start any kind of scripts at given events.
Simply put your script in a suitable folder and pyLoad will execute it at the given events and pass some arguments to them.

-->  Note: Scripts, which starts with # will be ignored!
For Example: #converter.sh will not be executed.

-->  Note: You have to restart pyload when you change script names or locations.

Below you see the list of arguments, which are passed to the scripts.

## Argument list ##

download_preparing: pluginname url

download_finished: pluginname url filename filelocation

package_finshed: packagename packagelocation

before_reconnect: oldip

after_reconnect: newip