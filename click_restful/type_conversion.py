import click
import click.types

CLICK_TYPE_MAPPING = {
    click.types.STRING: str,
    click.types.INT: int,
    click.types.FLOAT: float,
    click.types.BOOL: bool,
    click.types.UUID: str,
}


OAS_TYPE_MAPPING = {
    str: 'string',
    int: 'integer',
    float: 'number',
    bool: 'boolean'
}


def reverse_click_type(param: click.Parameter):
    """The inverse of click.types.convert_type"""
    return CLICK_TYPE_MAPPING[param.type]


def click_type_to_oas(param: click.Parameter) -> str:
    base_type = CLICK_TYPE_MAPPING[param.type]
    oas_name = OAS_TYPE_MAPPING[base_type]
    return oas_name


