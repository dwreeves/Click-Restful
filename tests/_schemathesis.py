"""This module overwrites some stuff inside schemathesis.lazy so that it works for methods."""
from inspect import signature
from typing import Callable, Optional, Union
from _pytest.fixtures import FixtureRequest
from pytest_subtests import SubTests
from schemathesis.types import Filter, NotSet
from schemathesis.utils import NOT_SET
from schemathesis.lazy import LazySchema, get_test, _get_node_name, get_schema, run_subtest, get_fixtures


class LazySchemaMethods(LazySchema):

    def parametrize(  # pylint: disable=too-many-arguments
        self,
        method: Optional[Filter] = NOT_SET,
        endpoint: Optional[Filter] = NOT_SET,
        tag: Optional[Filter] = NOT_SET,
        operation_id: Optional[Filter] = NOT_SET,
        validate_schema: Union[bool, NotSet] = NOT_SET,
        skip_deprecated_endpoints: Union[bool, NotSet] = NOT_SET,
    ) -> Callable:
        if method is NOT_SET:
            method = self.method
        if endpoint is NOT_SET:
            endpoint = self.endpoint
        if tag is NOT_SET:
            tag = self.tag
        if operation_id is NOT_SET:
            operation_id = self.operation_id

        def wrapper(func: Callable) -> Callable:
            def test(request: FixtureRequest, subtests: SubTests) -> None: # <-- Line changed
                """The actual test, which is executed by pytest."""
                if hasattr(test, "_schemathesis_hooks"):
                    func._schemathesis_hooks = test._schemathesis_hooks  # type: ignore
                schema = get_schema(
                    request=request,
                    name=self.fixture_name,
                    method=method,
                    endpoint=endpoint,
                    tag=tag,
                    operation_id=operation_id,
                    hooks=self.hooks,
                    test_function=func,
                    validate_schema=validate_schema,
                    skip_deprecated_endpoints=skip_deprecated_endpoints,
                )
                fixtures = get_fixtures(func, request)
                # Changing the node id is required for better reporting - the method and endpoint will appear there
                node_id = subtests.item._nodeid
                settings = getattr(test, "_hypothesis_internal_use_settings", None)
                tests = list(schema.get_all_tests(func, settings))
                request.session.testscollected += len(tests)
                for _endpoint, sub_test in tests:
                    actual_test = get_test(sub_test)
                    subtests.item._nodeid = _get_node_name(node_id, _endpoint)
                    run_subtest(_endpoint, fixtures, actual_test, subtests)
                subtests.item._nodeid = node_id

            # Get this to work on instance methods
            # can implement better solution
            # https://stackoverflow.com/questions/19314405/how-to-detect-is-decorator-has-been-applied-to-method-or-function
            sig = signature(func)
            if len(sig.parameters) >= 1 and list(sig.parameters.keys())[0] == 'self':
                def test_method(self, request: FixtureRequest, subtests: SubTests) -> None:
                     return test(request, subtests)
                dec = test_method
            else:
                dec = test

            # Needed to prevent a failure when settings are applied to the test function
            dec.is_hypothesis_test = True  # type: ignore

            return dec

        return wrapper
