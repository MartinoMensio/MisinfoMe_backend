import flask
from flask import send_from_directory, redirect, url_for
import flask_restplus
import os

# the swaggerui is usually served with static files with a path '/swaggerui'
# but we can't serve that path because of the '/misinfo' prefix
# so we need to modify the behaviour of the apidoc
modified_apidoc = flask_restplus.apidoc.Apidoc('restplus_doc_modified',
            __name__,
            template_folder='templates',
            # here lies the trick, to get the static files
            static_folder=os.path.dirname(flask_restplus.__file__)+'/static',
            # and serve with this new path
            static_url_path='/misinfo/api/swaggerui',)

# this will reply to the GET requests on the new path
@modified_apidoc.add_app_template_global
def swagger_static(filename):
    #print('swagger_static', filename)
    return url_for('restplus_doc_modified.static', filename=filename)



def configure_static_resources(base_url, app: flask.Flask, api: flask_restplus.Api):
    #app_url = base_url + '/app'
    app_url = base_url

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

    @app.route(base_url + '/favicon.ico')
    def favicon_helper():
        return send_from_directory('../app', 'favicon.ico')


    @app.route(base_url + '/assets/<path:path>')
    def assets_helper(path):
        return send_from_directory('../app/assets', path)

    # @app.route('/')
    @app.route(base_url)
    @app.route(base_url + '/')
    #@app.route(app_url)
    def redirect_home():
        print('here in redirect_home')
        # this route is for sending the user to the homepage
        return redirect(base_url + '/home')


    @app.route('/static/<path:path>')
    # @app.route('/favicon.ico')
    def static_proxy_v2(path=None):
        # the static files
        print('here in static_proxy', path)
        # raise ValueError(path)
        return send_from_directory('../app_v2', path)

    @app.route('/<path:path>')
    @app.route('/home')
    def send_new_frontend(path=None):
        print(send_new_frontend, path)
        # raise ValueError(path)
        return send_from_directory('../app_v2', 'index.html')


    # we need to register the newly created blueprint for the documentation
    app.register_blueprint(modified_apidoc)
    # and overwrite this damn method, to have an internal url to specs_url (otherwise it weirdly creates a localhost in the template)
    flask_restplus.apidoc.ui_for = lambda self: flask.render_template('swagger-ui.html',
        title=api.title,
        specs_url='/misinfo/api/swagger.json')

    """
    # some experiments
    @app.route(base_url + '/apiaaaa')
    def get_swaggerui():
        print('get homepage of swaggerui')
        return flask.render_template('swagger-ui.html', title=api.title,
                           specs_url='/misinfo/api/swagger.json')
        #return flask_restplus.apidoc.ui_for(api)
    """
