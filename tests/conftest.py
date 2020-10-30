import shlex
import click
from click.testing import CliRunner
import pytest


@pytest.fixture
def runner():
    return CliRunner()


class ClickCommandTestCase(object):
    cmd: click.Command
    routes: list
    inputs: list
    outputs: list
    stdouts: list

    @property
    def _zipped(self):
        enum = range(len(self.inputs))
        for i in zip(enum, self.routes, self.inputs, self.outputs, self.stdouts):
            yield i

    def _call_cmd(self, _input):
        if isinstance(_input, str):
            def _strip_dashes(s):
                while s.startswith('-'):
                    s = s[1:]
                return s

            _input = shlex.split(_input)
            _input = {
                _strip_dashes(k): True if v.startswith('-') else v
                for k, v in zip(_input, _input[1:] + ['--'])
                if k.startswith('-')
            }
            for p in self.cmd.params:
                _input[p.name] = p.type.convert(_input[p.name], None, None)

        if isinstance(_input, dict):
            return self.cmd.callback(**_input)
        else:
            return self.cmd.callback(*_input)

    @property
    def _app(self):
        from click_restful import create_click_app
        app = create_click_app(self.cmd)
        return app

    @pytest.fixture
    def app(self):
        return self._app

    def test_io(self, subtests):
        for _enum, _route, _input, _output, _stdout in self._zipped:
            with subtests.test(msg=f'{self}:test_io:{_enum}', i=_enum):
                assert self._call_cmd(_input) == _output

    def test_stdout(self, subtests, runner):
        for _enum, _route, _input, _output, _stdout in self._zipped:
            with subtests.test(msg=f'{self}:test_stdout:{_enum}', i=_enum):
                result = runner.invoke(self.cmd, _input)
                assert result.output == _stdout

    def test_placement_in_app(self, app):
        client = app.test_client()
        assert client.get('/').status_code == 302

    def test_as_endpoint(self, subtests, app):
        client = app.test_client()
        for _enum, _route, _input, _output, _stdout in self._zipped:
            with subtests.test(msg=f'{self}:test_as_endpoint:{_enum}', i=_enum):
                assert client.get(_route).status_code < 400
