from flask import send_from_directory, redirect

def configure_static_resources(base_url, app):
    app_url = base_url + '/app'

    @app.route(base_url + '/static/<path:path>')
    def static_proxy(path):
        # the static files
        print('here in static_proxy', path)
        return send_from_directory('../app', path)

    @app.route(app_url + '/<path:path>')
    @app.route(app_url + '/')
    def deep_linking(path=None):
        # send the angular application, mantaining the state informations (no redirects)
        print('here in deep_linking')
        return send_from_directory('../app', 'index.html')

    @app.route('/')
    @app.route(base_url)
    @app.route(base_url + '/')
    @app.route(app_url)
    def redirect_home():
        print('here in redirect_home')
        # this route is for sending the user to the homepage
        return redirect(app_url + '/home')
