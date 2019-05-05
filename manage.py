#!/usr/bin/env python3.7

import logging
import click
import uvicorn

log = logging.getLogger(__name__)


@click.group()
def cli():
    logging.basicConfig(level=logging.INFO)


@cli.command()
@click.option('--reloader/--no-reloader', '-r', default=False)
def serve(reloader):
    print('Running webserver on 0.0.0.0:32000')
    uvicorn.run('chat.http:app', host='0.0.0.0', port=32000, reload=reloader, debug=True)


@cli.command()
def shell():
    namespace = {}

    try:
        from IPython.terminal.interactiveshell import TerminalInteractiveShell
        console = TerminalInteractiveShell(user_ns=namespace)
        print('Starting iPython Shell')
    except ImportError:
        import code
        import rlcompleter
        c = rlcompleter.Completer(namespace)

        # Setup readline for autocomplete.
        try:
            # noinspection PyUnresolvedReferences
            import readline
            readline.set_completer(c.complete)
            readline.parse_and_bind('tab: complete')
            readline.parse_and_bind('set show-all-if-ambiguous on')
            readline.parse_and_bind(r'"\C-r": reverse-search-history')
            readline.parse_and_bind(r'"\C-s": forward-search-history')

        except ImportError:
            pass

        console = code.InteractiveConsole(namespace)
        print('Starting Poverty Shell (install IPython to use improved shell)')

    from chat.http import app

    with app.app_context():
        console.interact()


if __name__ == '__main__':
    cli(obj={})
