"""Right now struggling to get `test_api` to work as a fixture. The problem
seems to be that it thinks the test case class is a
pytest.fixtures.FixtureRequest object, and tries to call all of its methods.
"""
import pytest
import schemathesis
import hypothesis
from .test_commands import command_specs


@pytest.fixture #(params=command_specs)
def command_spec():
    return command_specs[0]()


@pytest.fixture
def schema_fixture(command_spec):
    app = command_spec._app
    _schema = schemathesis.from_wsgi('/click_restful.json', app)
    return _schema


schema = schemathesis.from_pytest_fixture('schema_fixture')


@pytest.mark.filterwarnings("ignore:^.*'subtests' fixture.*$")
@schema.parametrize()
@hypothesis.settings(deadline=None)
def test_api(case):
    """Test the API against the OpenAPI specification."""
    response = case.call_wsgi()
    case.validate_response(response)
