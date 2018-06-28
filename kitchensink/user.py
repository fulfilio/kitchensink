import flask
from fulfil_client import model
from fulfil_client.model import StringType, BooleanType, IntType
from flask_login import UserMixin, login_user, logout_user
from oauthlib.oauth2 import InvalidGrantError
from .extensions import fulfil, login_manager
from .utils import get_oauth_session

blueprint = flask.Blueprint('user', __name__, url_prefix="/user")
public = flask.Blueprint('public', __name__, url_prefix="")
Model = model.model_base(fulfil)


def error_500(e):
    """500 Error Page
    """
    return flask.render_template("500.html"), 500


@public.route('/')
def home():
    return flask.render_template('home.html')


class User(UserMixin, Model):
    """
    A user of the app.
    """
    __model_name__ = 'res.user'

    id = IntType(required=True)
    login = StringType(required=True)
    name = StringType(required=True)
    active = BooleanType(required=True)

    @property
    def is_active(self):
        return self.active

    def get_id(self):
        return self.id and str(self.id)


@login_manager.user_loader
def load_user(user_id):
    if user_id:
        return User.get_by_id(int(user_id))


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    oauth_session = get_oauth_session()
    next = flask.request.args.get('next')
    authorization_url, state = oauth_session.create_authorization_url(
        redirect_uri=flask.url_for(
            '.authorized',
            next=next,
            _external=True
        ),
        scope=['stock.shipment.out:read']
    )
    flask.session['oauth_state'] = state

    return flask.redirect(authorization_url)


@blueprint.route('/authorized')
def authorized():
    state = flask.request.args.get('state')
    oauth_state = flask.session.pop('oauth_state', None)
    if not oauth_state or oauth_state != state:
        # Verify if state is there in session
        flask.abort(401)

    code = flask.request.args.get('code')
    oauth_session = get_oauth_session()
    try:
        token = oauth_session.get_token(code=code)
    except InvalidGrantError:
        return flask.redirect(flask.url_for('public.home'))
    if not token:
        flask.abort(400)

    user = User(
        id=token['associated_user']['id'],
        login=token['associated_user']['email'],
        name=token['associated_user']['name'],
        active=True
    )
    flask.session['FULFIL_ACCESS_TOKEN'] = token['access_token']
    login_user(user)
    next = flask.request.args.get('next')

    return flask.redirect(next or flask.url_for('public.home'))


@blueprint.route("/logout")
def logout():
    logout_user()
    return flask.redirect(flask.url_for('public.home'))
