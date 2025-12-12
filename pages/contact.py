import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from dash import dcc, html, Input, Output, State, callback, no_update, clientside_callback
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import re
import json
import requests

from configs import URL_BASE, EMAIL, EMAIL_PWD, EMAIL_RECIPIENT

# --- Register page --- #
dash.register_page(
    __name__,
    path='/contact',
    title='SurvivalGenie2.0 Contact Us',
    location="navbar"
)

app = dash.get_app()

CONTACT_FORM = dbc.Form([
    dbc.Row([
        dbc.Label("Your Email:", html_for="contact-email", width=2),
        dbc.Col(
            dbc.Input(type="email", id="contact-email", placeholder="Enter email", required=True),
            width=9)
    ],className="mb-3"),
    dbc.Row([
        dbc.Label("Subject:", html_for="contact-subj", width=2),
        dbc.Col(
            dbc.Input(id="contact-subj", placeholder="Subject", required=True),
            width=9)
    ],className="mb-3"),
    dbc.Row([
        dbc.Label("Contents:", html_for="contact-content", width=2),
        dbc.Col(
            dbc.Textarea(id="contact-content", required=True, placeholder="Contents that you want to send to our team.",style={"height":"150px"}),
            width=9)
    ],className="mb-3"),
    dbc.Row(
        dbc.Col(
            [html.Div(id='contact-recaptcha'),
            html.Div(id='contact-recaptcha-response',style={'display':'none'}),
            dbc.Button("Submit",id="contact-submit",type="submit",n_clicks=0)],
            width=4,class_name="d-grid"),
        justify="center")
], id = "contact-form")


# --- Components --- #
CONTACT = dbc.Card(
    dbc.CardBody(
        [
            dbc.Spinner(id="contact-sending",
                children=CONTACT_FORM),
        ],
    )
)

# --- Layout --- #
def layout():
    layout = dbc.Container([
        html.Br(),
        dbc.Row(
            [dbc.Col([
                html.H1("Contact", className="card-title"),
                html.Br(),
                html.P(["⭐Check out our ", html.A("new lab page!", href="https://bhasinlab.org/", target="_blank")], className="card-text", style={"font-size": "1.1rem"}),#SurvivalGenie2 support gmail.
                CONTACT
            ],
                sm=dict(size=12),
                lg=dict(size=8))],
            justify="center",
        ),
        dcc.ConfirmDialog(
                id='confirm-send-contact-msg',
                message='The form has been submitted.',
            ),
        ],
    fluid=True,
    )
    return layout


# ------------ call backs ------------------
clientside_callback(
        """
        async function(n_clicks) {
            if (n_clicks==0){
                grecaptcha.render('contact-recaptcha', {'sitekey' : '_sitekey'});
            }
            if (n_clicks > 0){
                var recaptcha_response = document.getElementById('g-recaptcha-response');
                return recaptcha_response.value;
            }
        }
        """.replace('_sitekey',app.server.config['RECAPTCHA_SITEKEY']),
        
        Output('contact-recaptcha-response', 'children'), 
        Input("contact-submit", 'n_clicks')
    )

@callback(
    Output("contact-sending","children"),
    Output('confirm-send-contact-msg', 'displayed'),
    Output('confirm-send-contact-msg', 'message'),
    Output('hidden-div-for-redirect-callback', 'children', allow_duplicate=True),
    Input("contact-submit", "n_clicks"),
    Input('contact-recaptcha-response','children'),
    State("contact-email", "value"),
    State("contact-subj", "value"),
    State("contact-content", "value"),
    prevent_initial_call=True
)
def submit_report(click, recaptcha_response, user, subj, text):
    if not click:
        return no_update
    if recaptcha_response is None or recaptcha_response.strip() == '':
        return no_update
    email_rgx = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if not re.match(email_rgx,user):
        return no_update, True, 'Invalid Email Address', no_update

    request_headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8" }
    request_url = 'https://www.google.com/recaptcha/api/siteverify?secret={0}&response={1}'.format(app.server.config['RECAPTCHA_SECRET'],recaptcha_response)
    response = requests.post(request_url,headers=request_headers)

    response_json = json.loads(response.text)    

    if not response_json['success']:
        return no_update
        
    # form the message
    msg_body = f"User: {user}\nForm contents:\n{text}"
    msg = MIMEMultipart()
    msg['Subject'] = f"[SurvivalGenie2-Sys-Contact] {subj}"
    msg['From'] = EMAIL
    msg['To'] = ', '.join(EMAIL_RECIPIENT)
    msg.attach(MIMEText(msg_body))

    try:
        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.ehlo()
        smtp.starttls()  # tell server we want to communicate with TLS encryption
        smtp.login(EMAIL, EMAIL_PWD)  # login to our email server
        smtp.send_message(msg, EMAIL, EMAIL_RECIPIENT)
        smtp.quit()
    except smtplib.SMTPResponseException:
        return no_update, True, 'Something went wrong. please try later on use our Github page.', no_update


    return no_update, True, 'The form has been submitted.', dcc.Location(pathname=URL_BASE+"home", id="")