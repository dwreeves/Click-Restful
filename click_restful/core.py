import os
import warnings
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

    def __init__(self, style: str = 'plain', silent: bool = True):
        self.record = ''
        self.style = style
        self.silent = True
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
        if self.silent:
            with open(os.devnull, 'w') as f:
                kwargs['file'] = f
                return self._old_echo(**kwargs)
        else:
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

    try:
        with flask.current_app.app_context():
            url_prefix = flask.current_app.extensions['click_restful'].url_prefix
    except (RuntimeError, KeyError):
        url_prefix = None
    _add_prefix = lambda s: s if url_prefix is None else f'{url_prefix}/{s}'

    bp = flask.Blueprint(cmd.name, __name__, url_prefix=_add_prefix(f'/{cmd.name}'))
    bp.cli.add_command(cmd)

    all_commands = getattr(cmd, 'commands', {'': cmd})

    for _name, _cmd in all_commands.items():

        def rest():
            kwargs = {
                i.name: i.default
                for i in _cmd.params
            }

            # Typecast
            req_params = {
                k: _typecast(v, kwargs[k])
                for k, v in flask.request.args.items()
            }

            kwargs.update(req_params)

            with Logger() as log:
                res = _cmd.callback(**kwargs)

            return _create_response(res=res, log=log, jsonify=jsonify)

        rest.__doc__ = openapi_yaml(cmd)
        rest.__name__ = _name
        bp.add_url_rule(f'/{_name}', _name, view_func=rest)

    return bp


class ClickRestful(object):
    """

    :param app:
    :param config_prefix:
    """

    def __init__(
            self,
            app: flask.Flask = None,
            url_prefix: str = None,
            config_prefix: str = 'CLICK_RESTFUL_'
    ):
        _add_prefix = lambda s: s if url_prefix is None else f'{url_prefix}/{s}'
        self.app = None
        self.swagger = None
        self.url_prefix = None
        self.swagger_config = {
            'headers': [],
            'specs': [{
                'endpoint': 'click_restful_swagger',
                'route': _add_prefix('/click_restful.json'),
                'rule_filter': lambda rule: True,
                'model_filter': lambda tag: True,
            }],
            'static_url_path': _add_prefix('/flasgger_static'),
            'swagger_ui': True,
            'specs_route': _add_prefix('/apidocs/')
        }
        self.template = {
            'info': {
                'title': 'Click RESTful App',
                'description': '',
                'version': '0.0',
            }
        }
        self.config_prefix = config_prefix
        if app:
            self.init_app(app)

    def init_app(self, app: flask.Flask):
        self.app = app
        app.extensions.setdefault('click_restful', self)

        with warnings.catch_warnings():
            warnings.simplefilter('ignore', category=DeprecationWarning)
            from flasgger import Swagger

        self.swagger = Swagger(
            app, config=self.swagger_config, template=self.template)


def create_click_app(cmd=None, **kwargs):
    app = flask.Flask(__name__)

    with app.app_context():
        click_rest = ClickRestful()
        click_rest.init_app(app)
        if cmd:
            bp = click_to_blueprint(cmd, **kwargs)
            app.register_blueprint(bp)

    @app.route('/')
    def index():
        return flask.redirect(flask.url_for('flasgger.apidocs'))

    return app


def run_click_app(cmd, host=None, port=None, **kwargs):
    app = create_click_app(cmd, **kwargs)
    app.run(host=host, port=port)
