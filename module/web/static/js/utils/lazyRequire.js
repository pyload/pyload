// Define the module.
define(
	[
		"require", "underscore"
	],
	function( require, _ ){


		// Define the states of loading for a given set of modules
		// within a require() statement.
		var states = {
			unloaded: "UNLOADED",
			loading: "LOADING",
			loaded: "LOADED"
		};


		// Define the top-level module container. Mostly, we're making
		// the top-level container a non-Function so that users won't
		// try to invoke this without calling the once() method below.
		var lazyRequire = {};


		// I will return a new, unique instance of the requrieOnce()
		// method. Each instance will only call the require() method
		// once internally.
		lazyRequire.once = function(){

			// The modules start in an unloaded state before
			// requireOnce() is invoked by the calling code.
			var state = states.unloaded;
            var args;

			var requireOnce = function(dependencies, loadCallback ){

				// Use the module state to determine which method to
				// invoke (or just to ignore the invocation).
				if (state === states.loaded){
					loadCallback.apply(null, args);

				// The modules have not yet been requested - let's
				// lazy load them.
				} else if (state !== states.loading){

					// We're about to load the modules asynchronously;
					// flag the interim state.
					state = states.loading;

					// Load the modules.
					require(
						dependencies,
						function(){

                            args = arguments;
							loadCallback.apply( null, args );
                            state = states.loaded;


						}
					);

				// RequireJS is currently loading the modules
				// asynchronously, but they have not finished
				// loading yet.
				} else {

					// Simply ignore this call.
					return;

				}

			};

			// Return the new lazy loader.
			return( requireOnce );

		};


		// -------------------------------------------------- //
		// -------------------------------------------------- //

        // Set up holder for underscore
        var instances = {};
        _.requireOnce = function(dependencies, loadCallback) {
            if (!_.has(instances, dependencies))
                instances[dependencies] = lazyRequire.once();

            return instances[dependencies](dependencies, loadCallback)
        };


		// Return the module definition.
		return( lazyRequire );
	}
);