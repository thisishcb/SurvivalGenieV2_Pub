import uuid
import dash
# import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, no_update, State, DiskcacheManager, CeleryManager
# from flask import Flask, render_template, redirect, request
# from flask_sqlalchemy import SQLAlchemy
# import sys
import os
import logging
from logging.handlers import RotatingFileHandler

import dash_bootstrap_components as dbc
from flask import send_from_directory #, abort
# import base64
from navbar import create_navbar
from server import server, task_tb, db

from configs import URL_BASE, SRV_HOST, SRV_PORT, TEST, CACHE_PATH, REDIS_URL, DATA_PATH

BOOTSTRAP_CSS = "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" #"assets/bootstrap.css" # https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
# CUSTOM_CSS = "assets/custom_css.css"
# CUSTOM_JS = "assets/custom-script.js"
APP_TITLE = "SurvivalGenie2.0"

if not TEST:
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery
    celery_app = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)
    celery_app.conf.broker_connection_retry_on_startup = True 
    background_callback_manager = CeleryManager(celery_app)

else:
    # Diskcache for non-production apps when developing locally
    import diskcache
    cache = diskcache.Cache(CACHE_PATH)
    background_callback_manager = DiskcacheManager(cache)

external_srcs = dict(
    stylesheets = [dbc.themes.BOOTSTRAP], #BOOTSTRAP_CSS
    scripts = ['https://www.google.com/recaptcha/api.js?render=explicit', "https://cdn.jsdelivr.net/npm/bootstrap@5.3.6/dist/js/bootstrap.bundle.min.js", 'https://cdn.jsdelivr.net/npm/dom-to-image@2.6.0/dist/dom-to-image.min.js']
)

if TEST:
    app = dash.Dash(
            server=server,
            external_stylesheets=external_srcs["stylesheets"], 
            external_scripts = external_srcs["scripts"],
            use_pages=True, 
            url_base_pathname=URL_BASE, # url_base_pathname default to requests_pathname_prefix
            # requests_pathname_prefix=URL_BASE,
            title=APP_TITLE, 
            suppress_callback_exceptions=True,# not TEST, # True for deploying
            background_callback_manager=background_callback_manager,
            meta_tags=[
                {
                    "name": "viewport",
                    "content": "width=device-width, initial-scale=1.0",
                }
            ],
        )

    @server.route(f'{URL_BASE}example_files/<path:filename>')
    def serve_my_static_files(filename):
        return send_from_directory(os.path.join(DATA_PATH, "example_in"), filename, mimetype='text/plain')

else:
    app = dash.Dash(
        server=server,
        external_stylesheets=external_srcs["stylesheets"], 
        external_scripts = external_srcs["scripts"],
        use_pages=True, 
        requests_pathname_prefix=URL_BASE,
        title=APP_TITLE, 
        suppress_callback_exceptions=True,# not TEST, # True for deploying
        background_callback_manager=background_callback_manager,
        meta_tags=[
            {
                "name": "viewport",
                "content": "width=device-width, initial-scale=1.0",
            }
        ],
    )

    @server.route(f'/example_files/<path:filename>')
    def serve_my_static_files(filename):
        return send_from_directory(os.path.join(DATA_PATH, "example_in"), filename, mimetype='text/plain')

# app.scripts.config.serve_locally = True
# app.css.config.serve_locally = True

# https://stackoverflow.com/questions/65274912/how-to-set-an-google-opt-out-cookie-for-google-analytics-4-not-universal-one
# <a href="javascript:gaOptout()">Click here to opt-out of Google Analytics</a>

# --- Google analytics --- #
app.index_string = f"""
<!DOCTYPE html>
<html>
    <head>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-7F1JEPVWP8"></script>
        <script>
        var disableStr = 'ga-disable-G-7F1JEPVWP8';
        if (document.cookie.indexOf(disableStr + '=true') > -1) {{
            window['ga-disable-G-7F1JEPVWP8'] = true;
        }}
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());

        gtag('config', 'G-7F1JEPVWP8');

        function gaOptout() {{
        document.cookie = disableStr + '=true; expires=Thu, 31 Dec 2099 23:59:59 UTC; path=/';
        window[disableStr] = true;
        }}
        </script>

        {{%metas%}}
        <title>{APP_TITLE}</title>
        {{%favicon%}}
        {{%css%}}
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
        
    </body>
</html>
"""

# --- Navbar --- #
NAVBAR = create_navbar()

def framework_layout():
    session_id = uuid.uuid4().hex
    return html.Div(
    [
        dcc.Location(id='url'),
        html.Div(id="hidden-div-for-redirect-callback", style={'display': 'none'}),
        NAVBAR,
        dash.page_container,
        dcc.Store(id="storesession", storage_type="session",data=dict()),
        # dcc.Store(id="user-info", storage_type="session",data=request.remote_addr),
        dcc.Store(id="session-id", storage_type="session",data=session_id),
    ]
)
# --- Layout --- #
app.layout = framework_layout
    
# ---  callbacks --- # 
@callback(
    Output("show-session-id", "children"),
    Input('session-id', 'data'),
)
def display_session_id(ssid):
    return ssid


@callback(
    Output('hidden-div-for-redirect-callback', 'children', allow_duplicate=True),
    Input('url', 'pathname'),
    State('session-id', 'data'),
    prevent_initial_call = True
)
def re_dir(url,ssid):
    # app.logger.info(f"---{ssid}---")
    if url in ['/SurvivalGenie2/', '/SurvivalGenie2']:
        return dcc.Location(pathname=URL_BASE+"home", id="")
    if "result_visualization" in url:
        task = db.session.get(task_tb, ssid)
        if not task:
            return dcc.Location(pathname=URL_BASE+"home", id="")
        if task.is_finished():
            task.add_visit()
            db.session.commit()
    return no_update

# if TEST:
#     @callback(Output('hidden-div-for-redirect-callback', 'children',allow_duplicate=True),
#             Input('url', 'pathname'),
#             Input('storesession', 'data'),
#             Input('user-info', 'data'),
#             Input('session-id', 'data'),
#             prevent_initial_call=True)
#     def check_user(pname, data, user_info, ssid):
#         print(pname, ssid, user_info, str(data))
#         return no_update
        # if pname not in ["/",""] and \
        #     not ("email" in user_info and "affilitation" in user_info):
        #     return dcc.Location(pathname="/", id="")

# @server.errorhandler(404)
# def page_not_found(error):
#     return render_template("404.html", title="Page not found")

# --- Launch app --- #
if __name__ == '__main__':
    handler = RotatingFileHandler(os.path.join(CACHE_PATH,"SurvGenieV2Running.log"), maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(host=SRV_HOST, port=SRV_PORT, debug=TEST)
    # app.run(host='192.168.1.66', port='8020', debug=True)
