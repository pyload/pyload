'use strict';
var LIVERELOAD_PORT = 35729;
var lrSnippet = require('connect-livereload')({port: LIVERELOAD_PORT});
var mountFolder = function(connect, dir) {
    return connect.static(require('path').resolve(dir));
};
var fs = require('fs');
var path = require('path');

// # Globbing
// for performance reasons we're only matching one level down:
// 'test/spec/{,*/}*.js'
// use this if you want to recursively match all subfolders:
// 'test/spec/**/*.js'

module.exports = function(grunt) {
    // load all grunt tasks
    require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);

    // configurable paths
    var yeomanConfig = {
        app: 'app',
        dist: 'dist',
        banner: '/* Copyright(c) 2009-2017 The pyLoad Team */\n',
        protocol: 'http'
    };

    grunt.initConfig({
        yeoman: yeomanConfig,
        watch: {
            options: {
                nospawn: true
            },
            less: {
                files: ['<%= yeoman.app %>/styles/**/*.less'],
                tasks: ['less']
            },
            livereload: {
                options: {
                    livereload: LIVERELOAD_PORT
                },
                files: [
                    '<%= yeoman.app %>/**/*.html',
                    '{<%= yeoman.app %>}/styles/**/*.css',
                    '{.tmp,<%= yeoman.app %>}/scripts/**/*.js',
                    '<%= yeoman.app %>/images/{,*/}*.{png,jpg,jpeg,gif,webp,svg}'
                ]
            }
        },
        connect: {
            options: {
                port: 9000,
                // change this to '0.0.0.0' to access the server from outside
                hostname: 'localhost',
                protocol: '<%= yeoman.protocol %>'
            },
            livereload: {
                options: {
                    middleware: function(connect) {
                        return [
                            lrSnippet,
                            mountFolder(connect, '.tmp'),
                            mountFolder(connect, yeomanConfig.app)
                        ];
                    }
                }
            },
            test: {
                options: {
                    middleware: function(connect) {
                        return [
                            mountFolder(connect, '.tmp'),
                            mountFolder(connect, 'test')
                        ];
                    }
                }
            },
            dist: {
                options: {
                    middleware: function(connect) {
                        return [
                            mountFolder(connect, yeomanConfig.dist)
                        ];
                    }
                }
            }
        },
        open: { // Opens the webbrowser
            server: {
                path: '<%= yeoman.protocol %>://localhost:<%= connect.options.port %>'
            }
        },
        clean: {
            dist: {
                files: [
                    {
                        dot: true,
                        src: [
                            '.tmp',
                            '<%= yeoman.dist %>/*',
                            '!<%= yeoman.dist %>/.git*'
                        ]
                    }
                ]
            },
            server: '.tmp'
        },
        jshint: {
            options: {
                jshintrc: '.jshintrc'
            },
            all: [
                'Gruntfile.js',
                '<%= yeoman.app %>/scripts/**/*.js',
                '!<%= yeoman.app %>/scripts/vendor/*',
                'test/spec/{,*/}*.js'
            ]
        },
        mocha: {
            all: {
                options: {
                    run: true,
                    urls: ['http://localhost:<%= connect.options.port %>/index.html']
                }
            }
        },
        less: {
            options: {
                paths: [yeomanConfig.app + '/styles/common', yeomanConfig.app + '/styles/default']
                //dumpLineNumbers: true
            },
            dist: {
                files: [
                    {
                        expand: true, // Enable dynamic expansion.
                        cwd: '<%= yeoman.app %>/styles/', // Src matches are relative to this path.
                        src: ['**/main.less'], // Actual pattern(s) to match.
                        dest: '.tmp/styles', // Destination path prefix.
                        ext: '.css' // Dest filepaths will have this extension.
                    }
                ]
            }
        },
        // not used since Uglify task does concat,
        // but still available if needed
        /*concat: {
         dist: {}
         },*/
        requirejs: {
            dist: {
                // Options: https://github.com/jrburke/r.js/blob/master/build/example.build.js
                options: {
                    // `name` and `out` is set by grunt-usemin
                    baseUrl: yeomanConfig.app + '/scripts',
                    optimize: 'none',
                    // TODO: Figure out how to make sourcemaps work with grunt-usemin
                    // https://github.com/yeoman/grunt-usemin/issues/30
                    //generateSourceMaps: true,
                    // required to support SourceMaps
                    // http://requirejs.org/docs/errors.html#sourcemapcomments
                    preserveLicenseComments: false,
                    useStrict: true,
                    wrap: true,

                    // Delete already included files from dist
                    // TODO: For multiple modules it would delete to much files
                    done: function(done, output) {
                        var root = path.join(path.resolve('.'), yeomanConfig.app);
                        var parse = require('rjs-build-analysis').parse(output);
                        parse.bundles.forEach(function(bundle) {
                            var parent = path.relative(path.resolve('.'), bundle.parent);
                            bundle.children.forEach(function(f) {
                                // Skip templates
                                if (f.indexOf('hbs!') > -1) return;

                                var rel = path.relative(root, f);
                                var target = path.join(yeomanConfig.dist, rel);

                                if (target === parent)
                                    return;

                                if (fs.existsSync(target)) {
                                    console.log('Removing', target);
                                    fs.unlinkSync(target);

                                    // Remove the empty directories
                                    var files = fs.readdirSync(path.dirname(target));
                                    if (files.length === 0) {
                                        fs.rmdirSync(path.dirname(target));
                                        console.log('Removing dir', path.dirname(target));
                                    }

                                }
                            });
                        });
                        done();
                    }
                    //uglify2: {} // https://github.com/mishoo/UglifyJS2
                }
            }
        },
        rev: {
            dist: {
                files: {
                    src: [
                        // TODO only main script needs a rev
                        '<%= yeoman.dist %>/scripts/default.js',
                        '<%= yeoman.dist %>/styles/{,*/}*.css'
                    ]
                }
            }
        },
        useminPrepare: {
            options: {
                dest: '<%= yeoman.dist %>'
            },
            html: '<%= yeoman.app %>/index.html'
        },
        usemin: {
            options: {
                dirs: ['<%= yeoman.dist %>']
            },
            html: ['<%= yeoman.dist %>/*.html'],
            css: ['<%= yeoman.dist %>/styles/**/*.css']
        },
        imagemin: {
            dist: {
                files: [
                    {
                        expand: true,
                        cwd: '<%= yeoman.app %>/images',
                        src: '**/*.{png,jpg,jpeg}',
                        dest: '<%= yeoman.dist %>/images'
                    }
                ]
            }
        },
        svgmin: {
            dist: {
                files: [
                    {
                        expand: true,
                        cwd: '<%= yeoman.app %>/images',
                        src: '**/*.svg',
                        dest: '<%= yeoman.dist %>/images'
                    }
                ]
            }
        },
        htmlmin: {
            dist: {
                options: {
                    /*removeCommentsFromCDATA: true,
                     // https://github.com/yeoman/grunt-usemin/issues/44
                     //collapseWhitespace: true,
                     collapseBooleanAttributes: true,
                     removeAttributeQuotes: true,
                     removeRedundantAttributes: true,
                     useShortDoctype: true,
                     removeEmptyAttributes: true,
                     removeOptionalTags: true*/
                },
                files: [
                    {
                        expand: true,
                        cwd: '<%= yeoman.app %>',
                        src: ['*.html'],
                        dest: '<%= yeoman.dist %>'
                    }
                ]
            }
        },
        cssmin: {
            options: {
                banner: yeomanConfig.banner
            },
            dist: {
                expand: true,
                cwd: '<%= yeoman.dist %>',
                src: ['**/*.css', '!*.min.css'],
                dest: '<%= yeoman.dist %>',
                ext: '.css'
            }
        },
        uglify: { // JS min
            options: {
                mangle: true,
                report: 'min',
                preserveComments: false,
                banner: yeomanConfig.banner
            },
            dist: {
                expand: true,
                cwd: '<%= yeoman.dist %>',
                dest: '<%= yeoman.dist %>',
                src: ['**/*.js', '!*.min.js']
            }
        },
        compress: {
            main: {
                options: {
                    mode: 'gzip'
                },
                expand: true,
                cwd: '<%= yeoman.dist %>',
                dest: '<%= yeoman.dist %>',
                src: ['**/*.{js,css,html}']
            }
        },

        // Put files not handled in other tasks here
        copy: {
            //  Copy files from third party libraries
            stageComponents: {
                files: [
                    {
                        expand: true,
                        flatten: true,
                        cwd: '<%= yeoman.app %>',
                        dest: '.tmp/fonts',
                        src: [
                            '**/font-awesome/font/*'
                        ]
                    },
                    {
                        expand: true,
                        flatten: true,
                        cwd: '<%= yeoman.app %>',
                        dest: '.tmp/vendor',
                        src: [
                            '**/select2/select2.{png,css}',
                            '**/select2/select2-spinner.gif',
                            '**/select2/select2x2.png'
                        ]
                    }
                    // {
                        // expand: true,
                        // cwd: '<%= yeoman.app %>/modules/pyload-common',
                        // dest: '.tmp',
                        // src: [
                            // 'favicon.ico',
                            // 'images/*',
                            // 'fonts/*'
                        // ]
                    // }
                ]
            },

            dist: {
                files: [
                    {
                        expand: true,
                        dot: true,
                        cwd: '<%= yeoman.app %>',
                        dest: '<%= yeoman.dist %>',
                        src: [
                            '*.{ico,txt}',
                            'images/{,*/}*.{webp,gif}',
                            'templates/**/*.html',
                            'scripts/**/*.js',
                            'styles/**/*.css',
                            'fonts/*'
                        ]
                    }
                ]
            },

            tmp: {
                files: [
                    {
                        expand: true,
                        cwd: '.tmp/',
                        dest: '<%= yeoman.dist %>',
                        src: [
                            'fonts/*',
                            'images/*',
                            '**/*.{css,gif,png,js,html,ico}'
                        ]
                    }
                ]
            }
        },
        concurrent: {
            server: [
                'copy:stageComponents',
                'less'
            ],
            test: [
                'less'
            ],
            dist: [
                'imagemin',
                'svgmin',
                'htmlmin',
                'cssmin'
            ]
        }
    });

    grunt.registerTask('server', function(target) {
        if (target === 'dist') {
            return grunt.task.run(['build', 'connect:dist:keepalive']);
        }

        grunt.task.run([
            'clean:server',
            'concurrent:server',
            'connect:livereload',
            'watch'
        ]);
    });

    grunt.registerTask('test', [
        'clean:server',
        'concurrent:test',
        'connect:test',
        'mocha'
    ]);

    grunt.registerTask('build', [
        'clean:dist',
        'useminPrepare',
        'less',
        'copy', // Copy .tmp, modules, app to dist
        'requirejs', // build the main script and remove included scripts
        'concat',
        'concurrent:dist',  // Run minimisation
        'uglify', // minify js
        'rev',
        'usemin',
        'compress'
    ]);

    grunt.registerTask('default', [
        'jshint',
        // 'test',
        'build'
    ]);
};
