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
        'tags': [cmd.name],
        'summary': cmd.help,
        'parameters': all_parameters_to_oas(cmd),
        'responses': {'200': {
            'description': f'Output for {cmd.name!r}',
            'schema': {
                'id': 'click_response',
                'description': f'Output for {cmd.name!r}!',
                'required': ['status'],
                'type': 'object',
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
                        'description': 'Output of `click.echo()` calls.'
                    }
                }
            }
        }}
    }


def parameter_to_oas(param: click.Parameter):
    d = {
        'name': param.name,
        'in': 'query',
        'type': click_type_to_oas(param)
    }
    if hasattr(param, 'default') and param.default is not None:
        d['default'] = param.default

    if isinstance(param, click.Option):
        if desc := getattr(param, 'help', ''):
             d['description'] = desc

    return d


def all_parameters_to_oas(cmd: click.Command):
    return [parameter_to_oas(param) for param in cmd.params]
