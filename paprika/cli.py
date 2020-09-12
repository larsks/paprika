import click
import jinja2
import json
import logging
import os
import tabulate

from dataclasses import dataclass
from pathlib import Path

from paprika.api import Paprika

LOG = logging.getLogger(__name__)
LEVELS = ['WARNING', 'INFO', 'DEBUG']
DEFAULT_CONFIG_FILE = (
    Path(os.environ.get('XDG_CONFIG_HOME', '~')) /
    '.config' /
    'paprika.json'
).expanduser()
DEFAULT_ENDPOINT = 'https://www.paprikaapp.com/api/v1'
DEFAULT_WORKERS = 5
CONTEXT_SETTINGS = {
    'auto_envvar_prefix': 'PAPRIKA',
}


@dataclass
class Config:
    database: str = None
    paprika_username: str = None
    paprika_password: str = None
    endpoint: str = DEFAULT_ENDPOINT
    max_workers: int = DEFAULT_WORKERS


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('-f', '--config-file', default=DEFAULT_CONFIG_FILE)
@click.option('-d', '--database', default='recipes.db')
@click.option('-v', '--verbose', count=True, default=0)
@click.pass_context
def main(ctx, database, verbose, config_file):
    ctx.obj = Config()

    try:
        with open(config_file) as fd:
            config = json.load(fd)

        for k, v in config.items():
            if hasattr(ctx.obj, k):
                setattr(ctx.obj, k, v)
    except FileNotFoundError:
        pass

    if database:
        ctx.obj.database = database

    loglevel = (
        LEVELS[verbose] if verbose < len(LEVELS) else 'DEBUG'
    )

    logging.basicConfig(level=loglevel)


@main.command()
@click.pass_context
def debug(ctx):
    api = Paprika(ctx.obj)
    api.bind()
    api.debug()


@main.command()
@click.option('-i', '--ingredients', is_flag=True)
@click.option('-d', '--description', is_flag=True)
@click.argument('query')
@click.pass_context
def search(ctx, ingredients, description, query):
    api = Paprika(ctx.obj)
    api.bind()
    res = api.search(query,
                     search_ingredients=ingredients,
                     search_description=description)

    breakpoint()
    print(tabulate.tabulate(res))


@main.command()
@click.pass_context
def list(ctx):
    LOG.info('listing all recipes')
    api = Paprika(ctx.obj)
    api.bind()
    res = api.list()
    print(tabulate.tabulate([r['id'], r['name']] for r in res))


@main.command()
@click.option('-u', '--username')
@click.option('-p', '--password')
@click.pass_context
def fetch(ctx, username, password):
    LOG.info('fetching all recipes')
    if username:
        ctx.obj.paprika_username = username
    if password:
        ctx.obj.paprika_password = password

    api = Paprika(ctx.obj)
    api.bind()
    api.fetch()


@main.command()
@click.argument('recipe_id')
@click.pass_context
def render(ctx, recipe_id):
    LOG.info('rendering recipe %s', recipe_id)
    env = jinja2.Environment(loader=jinja2.PackageLoader('paprika'))
    template = env.get_template('recipe.html')
    api = Paprika(ctx.obj)
    api.bind()
    recipe = api.get_by_id(recipe_id)

    print(template.render(recipe=recipe['data']))


@main.command()
@click.argument('recipe_id')
@click.pass_context
def get(ctx, recipe_id):
    LOG.info('get recipe %s', recipe_id)
    api = Paprika(ctx.obj)
    api.bind()
    recipe = api.get_by_id(recipe_id)

    print(json.dumps(recipe['data'], indent=2))
