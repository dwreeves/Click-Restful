from typing import Any
from .openapi import openapi_yaml
import flask
import click
from functools import wraps


class Logger:
    """
    Parser for stdout. This works by overriding `click.echo`. Normal print
    statements are not captured.

    At the moment the log parser is not very smart, e.g. it doesn't capture
    manually defined ANSI escape codes, flushes, and doesn't differentiate
    between stdout and stderr.
    """

    OUTPUT_STYLES = {'plain', 'html'}

    def __init__(self, style: str = 'plain'):
        self.record = ''
        self.style = style
        self._old_echo = None

    def __enter__(self):
        self._old_echo = click.echo
        click.echo = self.echo
        return self

    def __exit__(self, *args):
        click.echo = self._old_echo
        self.echo = None

    @property
    def style(self):
        return self._style

    @style.setter
    def style(self, val: str):
        if val not in self.OUTPUT_STYLES:
            raise TypeError(f'{val!r} must be in {self.OUTPUT_STYLES!r}')
        self._style = val

    def _record_html(self, **kwargs):
        color = kwargs.get('color')
        parastart = f'<p style="color:{color};">' if color else '<p>'
        self.record += ''.join([
            parastart,
            kwargs['message'],
            '</p>'
        ])

    def _record_plain(self, **kwargs):
        if self.record == '':
            self.record = kwargs['message']
        else:
            self.record += '\n' + kwargs['message']

    @wraps(click.echo)
    def echo(self, message=None, file=None, nl=True, err=False, color=None):
        """
        Monkeypatched version of click.echo that basically intercepts calls,
        records to self.record, then calls the old version again.
        """
        kwargs = dict(message=message, file=file, nl=nl, err=err, color=color)
        if self.style == 'html':
            self._record_html(**kwargs)
        else:
            self._record_plain(**kwargs)
        return self._old_echo(**kwargs)


def _typecast(val, default):
    if default is not None:
        return type(default)(val)
    else:
        return val


def _create_response(res: Any, log: Logger, jsonify: bool):
    """
    Takes a bunch of information and puts together an appropriate response to return.
    :param res:
    :param log:
    :param jsonify:
    :return:
    """
    if jsonify:
        d = {'status': 'success', 'stdout': log.record}
        if res is not None:
            d['return'] = res
        return d
    elif res is not None:
        out = res
        mimetype = 'text/plain'
    else:
        out = log.record
        mimetype = f'text/{log.style}'
    return flask.Response(
        out,
        status=200,
        mimetype=mimetype
    )


def click_to_blueprint(
        cmd: click.Command,
        jsonify: bool = True,
        **kwargs
) -> flask.Blueprint:

    bp = flask.Blueprint(cmd.name, __name__, url_prefix=f'/{cmd.name}')
    bp.cli.add_command(cmd)

    def rest():
        kwargs = {
            i.name: i.default
            for i in cmd.params
        }

        # Typecast
        req_params = {
            k: _typecast(v, kwargs[k])
            for k, v in flask.request.args.items()
        }

        kwargs.update(req_params)

        with Logger() as log:
            res = cmd.callback(**kwargs)

        return _create_response(res=res, log=log, jsonify=jsonify)

    rest.__doc__ = openapi_yaml(cmd)
    bp.add_url_rule('/', 'rest', view_func=rest)

    return bp


class ClickRestful(object):
    """

    :param app:
    :param config_prefix:
    """

    def __init__(
            self,
            app: flask.Flask = None,
            config_prefix: str = 'CLICK_RESTFUL_'
    ):
        self.app = None
        self.swagger = None
        self.config_prefix = config_prefix
        if app:
            self.init_app(app)

    def init_app(self, app: flask.Flask):
        self.app = app
        app.extensions.setdefault('click_restful', self)

        from flasgger import Swagger
        self.swagger = Swagger(app)


def create_click_app(cmd, **kwargs):
    app = flask.Flask(__name__)
    click_rest = ClickRestful()
    click_rest.init_app(app)
    bp = click_to_blueprint(cmd, **kwargs)
    app.register_blueprint(bp)

    @app.route('/')
    def index():
        return flask.redirect(flask.url_for('flasgger.apidocs'))

    return app


def run_click_app(cmd, host=None, port=None, **kwargs):
    app = create_click_app(cmd, **kwargs)
    app.run(host=host, port=port)
