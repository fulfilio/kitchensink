import webbrowser
from fulfil_client.oauth import Session
import os


def get_token():
    Session.setup(
        os.environ['FULFIL_APP_ID'], os.environ['FULFIL_APP_SECRET']
    )
    session = Session(os.environ['FULFIL_SUBDOMAIN'])
    oauth_session = session
    authorization_url, state = oauth_session.create_authorization_url(
        redirect_uri='urn:ietf:wg:oauth:2.0:oob',
        scope=['sale.channel:read'],
        access_type='offline_access'
    )
    webbrowser.open(authorization_url)
    # paste code here
    code = input('paste authorization code here\n')
    token = oauth_session.get_token(code=code)
    return token


token = get_token()

token_print = """ \n\nToken(Please save this token into your environment as
            'FULFIL_OFFLINE_ACCESS_TOKEN'): """
print(token_print, token['offline_access_token'])
