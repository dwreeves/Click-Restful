# Click-RESTful

A framework tht turns Click CLIs into Flask RESTful APIs.

## Install

```shell
pip install Click-Restful
```

## Example:

Mostly a copy + paste from the Click README, but with two lines changed:

```python
import click
from click_restful import run_click_app

@click.command()
@click.option('--count', default=1, help='Number of greetings.')
@click.option('--name', prompt='Your name',
              help='The person to greet.')
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for x in range(count):
        click.echo('Hello %s!' % name)

if __name__ == '__main__':
    run_click_app(hello)
```

The Click README says to run `python hello.py --count=3`. Instead, we will open up a new terminal and run the following to start a web server:

```shell
python hello.py
```

And then in our original terminal, run the following:

```shell
>>> curl -X GET "http://127.0.0.1:5000/hello/?name=John&count=3"
{"status":"success","stdout":"Hello John!\nHello John!\nHello John!"}
```

Then, go to your browser: `http://127.0.0.1:5000/` and you will see a Swagger app. All of your Click CLI documentation is reflected in the app, and you can ping the endpoint to your liking from your browser.

## Caveat Emptor

**The API is currently not set in stone and is subject to breakage.** At the moment this should be considered a proof of concept more than anything else. When this message is removed from the README, the API will be considered more stable.

## Other Limitations

At the moment, there are 2 major downsides with this framework:

- Click-Restful only works for very basic `click.Command`s at the moment. It does _not_ work with `click.Group` objects and it may not work with advanced `click.Command`s.

- The standalone app created with `run_click_app` works and has good behavior. But the extension `ClickRestful()` is not currently available as a stable Flask extension. There are a lot of subtle nuances required to make this work properly with other apps.

Both of these things are a WIP and the end goal is for Click-Restful to work with existing apps in a friendly manner and for grouped commands to work intuitively and simply.
