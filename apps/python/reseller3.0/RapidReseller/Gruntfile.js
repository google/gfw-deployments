module.exports = function (grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        appDir: 'static',
        srcDir: 'src',
        bowerDir: 'bower_components',
        vendorDir: 'src/js/vendor',

        assets: {
            css: {
                vendor: [
                    '<%= bowerDir %>/bootstrap/dist/css/bootstrap.css',
                    '<%= bowerDir %>/bootstrap/dist/css/bootstrap-theme.css'
                ]
            },
            js: {
                vendor: [
                    '<%= bowerDir %>/jquery/jquery.js',
                    '<%= bowerDir %>/angular/angular.js',
                    '<%= bowerDir %>/angular-route/angular-route.js',
                    '<%= bowerDir %>/bootstrap/dist/js/bootstrap.js',
                    '<%= bowerDir %>/angular-bootstrap/ui-bootstrap.js',
                    '<%= bowerDir %>/angular-bootstrap/ui-bootstrap-tpls.js'
                ]
            }
        },

        concat: {
            vendor: {
                files: {
                    '<%= appDir %>/css/vendor.css': [
                        '<%= assets.css.vendor %>'
                    ],
                    '<%= appDir %>/js/vendor.js': [
                        '<%= assets.js.vendor %>'
                    ]
                }
            },
            app: {
                files: {
                    '<%= appDir %>/js/app.compiled.js': [
                        '<%= srcDir %>/js/app.js',
                        '<%= srcDir %>/js/routes.js',
                        '<%= srcDir %>/js/modules/*.js',
                        '<%= srcDir %>/js/config/*.js',
                        '<%= srcDir %>/js/controllers/*.js',
                        '<%= srcDir %>/js/directives/*.js',
                        '<%= srcDir %>/js/filters/*.js',
                        '<%= srcDir %>/js/services/*.js',
                        '<%= ngtemplates.app.dest %>'
                    ],
                    '<%= appDir %>/css/app.css': [
                        '<%= srcDir %>/css/*.css'
                    ]
                }
            }
        },

        clean: {
            dev: [
                '<%= appDir %>/js/app.compiled.js',
                '<%= appDir %>/js/app.templates.js'
            ],
            all: [
                '<%= appDir %>/js/*',
                '<%= appDir %>/css/*'
            ]
        },

        karma: {
            unit: {
                options: {
                    frameworks: ['jasmine'],
                    files: [
                        '<%= appDir %>/js/vendor.js',
                        '<%= bowerDir %>/angular-mocks/angular-mocks.js',
                        '<%= appDir %>/js/app.compiled.js',
                        '<%= appDir %>/js/app.templates.js',
                        '<%= srcDir %>/js/test/*.js'
                    ],
                    browsers: ['PhantomJS'],
                    reporters: ['dots'],
                    runnerPort: 9999,
                    autoWatch: true
                }
            }
        },

        ngmin: {
            app: {
                src: "<%= appDir %>/js/app.compiled.js",
                dest: "<%= appDir %>/js/app.compiled.js"
            },
            vendor: {
                src: '<%= appDir %>/js/vendor.js',
                dest: '<%= appDir %>/js/vendor.js'
            }
        },

        // uglify js for production
        uglify: {
            default: {
                files: {
                    '<%= appDir %>/js/app.compiled.js': [
                        '<%= appDir %>/js/app.compiled.js'
                    ],
                    '<%= appDir %>/js/vendor.js': [
                        '<%= appDir %>/js/vendor.js'
                    ]
                }
            }
        },

        ngtemplates: {
            app: {
                cwd: '<%= srcDir %>/',
                src: 'partials/*.html',
                dest: '<%= appDir %>/js/app.templates.js',
                options: {
                    module: '<%= pkg.name %>',
                    htmlmin:  {
                        collapseWhitespace: true,
                        collapseBooleanAttributes: true
                    }
                }
            }
        },

        watch: {
            scripts: {
                files: [
                    '<%= srcDir %>/js/**',
                    '<%= srcDir %>/js/*',
                    '<%= srcDir %>/partials/*'
                ],
                tasks: [
                    'build:dev'
                ]
            }
        },

        build: {
            dev: {},
            prod: {},
            all: {}
        }

    });

    // load grunt npm modules
    grunt.loadNpmTasks('grunt-contrib-clean');
    grunt.loadNpmTasks('grunt-contrib-copy');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-ngmin');
    grunt.loadNpmTasks('grunt-karma');
    grunt.loadNpmTasks('grunt-angular-templates');

    grunt.registerTask('dev', [
        'build:dev',
        'watch'
    ]);

    grunt.registerTask('tw', [
        'build:dev',
        'watch:karma'
    ]);

    // task for building main index page based on environment
    grunt.registerMultiTask('build', 'Build the app based on environment.', function () {
        grunt.task.run('clean:dev');
        grunt.task.run('ngtemplates');
        grunt.task.run('concat:app');

        if(this.target == "all" || this.target == "prod") {
            grunt.task.run('concat:vendor');
            grunt.task.run('ngmin');
        } else {
            grunt.task.run('ngmin:app');
        }

        if (this.target == 'prod') {
            grunt.task.run('uglify');
        }

    });

};

