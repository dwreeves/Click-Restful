"""OpenAPI specification related stuff."""
from .type_conversion import click_type_to_oas
import yaml
import click


def openapi_yaml(cmd: click.Command):
    d = construct_json_specification(cmd)
    d_yaml = yaml.dump(d)

    if cmd.help:
        return '\n---\n'.join([cmd.help, d_yaml])
    else:
        return d_yaml


def construct_json_specification(cmd: click.Command):
    return {
        'parameters': all_parameters_to_oas(cmd),
        'responses': {'200': {'schema': {'click_response': {
            'description': 'DESC_GOES_HERE',
            'type': 'object',
            'required': ['status'],
            'properties': {
                'status': {
                    'type': 'string',
                    'enum': ['success', 'failure'],
                    'description': 'Indication of whether the API call was a success or a failure.',
                },
                'return': {
                    'description': 'Value from return statement.'
                },
                'stdout': {
                    'type': 'string',
                    'output': 'Output of `click.echo()` calls.'
                }
            }
        }}}}
    }


def parameter_to_oas(param: click.Parameter):
    d = {
        'name': param.name,
        'in': 'query',
        'schema': {'type': click_type_to_oas(param)}
    }
    if hasattr(param, 'default') and param.default is not None:
        d['default'] = param.default

    if isinstance(param, click.Option):
        if hasattr(param, 'help') and param.help:
             d['description'] = param.help

    return d


def all_parameters_to_oas(cmd: click.Command):
    return [parameter_to_oas(param) for param in cmd.params]
