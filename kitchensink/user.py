import flask
from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
from fulfil_client import model
from fulfil_client.model import StringType, BooleanType
from flask_login import UserMixin, login_user
from .extensions import fulfil, login_manager

blueprint = flask.Blueprint('user', __name__, url_prefix="/user")
public = flask.Blueprint('public', __name__, url_prefix="")
Model = model.model_base(fulfil)


@public.route('/')
def home():
    return flask.render_template('home.html')


class User(UserMixin, Model):
    """
    A user of the app.
    """
    __model_name__ = 'res.user'

    login = StringType(required=True)
    name = StringType(required=True)
    active = BooleanType(required=True)

    @classmethod
    def authenticate(cls, login, password):
        response = cls.rpc.client.login(login, password)
        if response:
            return User.get_by_id(response[0])
        return None


@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(int(user_id))


class LoginForm(Form):
    """Login form."""

    login = StringField('Login', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        """Create instance."""
        super(LoginForm, self).__init__(*args, **kwargs)
        self.user = None

    def validate(self):
        """Validate the form."""
        initial_validation = super(LoginForm, self).validate()
        if not initial_validation:
            return False

        self.user = User.authenticate(self.login.data, self.password.data)
        message = None
        if not self.user:
            message = 'Invalid login credentials'

        elif not self.user.active:
            message = 'User account is not activated'

        if message:
            # XXX:  Can't find better way to add global form error
            self.login.errors.append(message)
            return False

        return True


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        login_user(form.user)

        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        return flask.redirect(next or flask.url_for('public.home'))
    return flask.render_template('login.html', form=form)
