//Install node.js, navigate to the js folder, and then run this command: "node r.js -o app.build.js"
({

  // Creates a js-optimized folder at the same folder level as your "js" folder and places the optimized project there
  dir: "../js-optimized",

  // Tells Require.js to look at desktop.js for all shim and path configurations
  mainConfigFile: 'config.js',

  // Modules to be optimized:
  modules: [

//    {
//      name: "mobile"
//    },

    {
      name: "default"
    }
  ]

})
