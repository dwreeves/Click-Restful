import pytest
import click
from .conftest import ClickCommandTestCase

# =============================================================================


@click.command()
def hello():
    click.echo('Hello World!')


class TestHelloWorld(ClickCommandTestCase):
    cmd = hello
    routes = ['/hello/']
    inputs = ['']
    outputs = [None]
    stdouts = ['Hello World!\n']


# =============================================================================


@click.command('hello')
@click.option('--count', default=1, help='Number of greetings.')
@click.option('--name', prompt='Your name',
              help='The person to greet.')
def hello2(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    count = min(count, 100)  # ADDED FOR SPEED
    for x in range(count):
        click.echo('Hello %s!' % name)


class TestHelloWorld2(ClickCommandTestCase):
    cmd = hello2
    routes = ['/hello?count=3&name=Bob']
    inputs = ['--count 3 --name Bob']
    outputs = [None]
    stdouts = ['Hello Bob!\nHello Bob!\nHello Bob!\n']


# =============================================================================


@click.group()
def cli():
    pass

@click.command()
def initdb():
    click.echo('Initialized the database')

@click.command()
def dropdb():
    click.echo('Dropped the database')

cli.add_command(initdb)
cli.add_command(dropdb)


class TestBasicGroup(ClickCommandTestCase):
    cmd = cli
    routes = ['/cli/initdb', '/cli/dropdb']
    inputs = ['initdb', 'dropdb']
    outputs = [None, None]
    stdouts = ['Initialized the database\n', 'Dropped the database\n']
