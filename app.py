import json
import uuid
import dash
# import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output, no_update, State
# from flask import Flask, render_template, redirect, request
# from flask_sqlalchemy import SQLAlchemy

from dash.long_callback import DiskcacheLongCallbackManager
import diskcache

# import base64
from navbar import create_navbar
from server import server, task_tb, db

from configs import URL_BASE, SRV_HOST, SRV_PORT, TEST, CACHE_PATH

BOOTSTRAP_CSS = "assets/bootstrap.css"
CUSTOM_CSS = "assets/custom_css.css"
APP_TITLE = "SurvivalGenie2.0"

cache = diskcache.Cache(CACHE_PATH)
long_callback_manager = DiskcacheLongCallbackManager(cache)

app = dash.Dash(
        __name__, 
        server=server,
        external_stylesheets=[BOOTSTRAP_CSS, CUSTOM_CSS], 
        use_pages=True, 
        # url_base_pathname=URL_BASE, # url_base_pathname default to requests_pathname_prefix
        requests_pathname_prefix=URL_BASE,
        title=APP_TITLE, 
        suppress_callback_exceptions=True,# not TEST, # True for deploying
        long_callback_manager=long_callback_manager,
        meta_tags=[
            {
                "name": "viewport",
                "content": "width=device-width, initial-scale=1.0",
            }
        ],
    )

# app.scripts.config.serve_locally = True
# app.css.config.serve_locally = True

# --- Google analytics --- #
app.index_string = f'''
<!DOCTYPE html>
<html>
    <head>
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
'''

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
    app.run(host=SRV_HOST, port=SRV_PORT, debug=TEST)