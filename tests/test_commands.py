import pytest
import click
from .conftest import ClickCommandTestCase


@click.command()
@click.option('--count', default=1, help='Number of greetings.')
@click.option('--name', prompt='Your name',
              help='The person to greet.')
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    count = min(count, 100)  # ADDED FOR SPEED
    for x in range(count):
        click.echo('Hello %s!' % name)


class TestHelloWorld(ClickCommandTestCase):
    cmd = hello
    routes = ['/hello/?count=3&name=Bob']
    inputs = ['--count 3 --name Bob']
    outputs = [None]
    stdouts = ['Hello Bob!\nHello Bob!\nHello Bob!\n']


command_specs = [TestHelloWorld]
