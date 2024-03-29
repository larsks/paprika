import code
import concurrent.futures
import logging
import requests

from datetime import datetime
from paprika.models import db, RecipeIndex, Recipe
from pony import orm

LOG = logging.getLogger(__name__)


class Paprika(requests.Session):
    def __init__(self, config):
        super().__init__()

        self.config = config
        self.session = requests.Session()
        self.auth = (config.paprika_username, config.paprika_password)

    def bind(self):
        LOG.debug("binding to database")
        db.bind(provider="sqlite", filename=self.config.database, create_db=True)
        db.generate_mapping(create_tables=True)

    def request(self, method, url, **kwargs):
        res = super().request(method, url, **kwargs)
        res.raise_for_status()
        return res.json()

    def list_recipes(self):
        url = f"{self.config.endpoint}/sync/recipes/"
        return self.get(url)

    def fetch_one_recipe(self, uid, index=None):
        url = f"{self.config.endpoint}/sync/recipe/{uid}/"
        return self.get(url), index

    def list_meals(self):
        url = f"{self.config.endpoint}/sync/meals/"
        return self.get(url)

    @orm.db_session
    def debug(self):
        api = self
        code.interact(local=locals())

    @orm.db_session
    def fetch(self):
        pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.config.max_workers,
        )

        recipes = self.list_recipes()
        tasks = []

        for recipe in recipes["result"]:
            LOG.debug("checking recipe uid %s", recipe["uid"])
            index = RecipeIndex.get(uid=recipe["uid"])

            if index is None or index.hash != recipe["hash"]:
                LOG.debug("recipe %s has changed", recipe["uid"])
                tasks.append(pool.submit(self.fetch_one_recipe, recipe["uid"], index))
            else:
                LOG.debug("recipe %s is unchanged", recipe["uid"])

        for future in concurrent.futures.as_completed(tasks):
            data, index = future.result()
            remote = data["result"]
            LOG.info("retrieved recipe %s (%s)", remote["uid"], remote["name"])

            if index:
                index.hash = remote["hash"]
                index.last_update = datetime.utcnow()
                recipe = Recipe[index]
                recipe.data = remote
                recipe.name = remote["name"]
            else:
                index = RecipeIndex(
                    uid=remote["uid"],
                    hash=remote["hash"],
                )

                Recipe(id=index, data=remote, name=remote["name"])

    @orm.db_session
    def search(self, query, search_ingredients=False, search_description=False):
        res = Recipe.select(lambda r: query in r.data["name"])

        return [r.to_dict() for r in res]

    @orm.db_session
    def list(self):
        return [r.to_dict() for r in Recipe.select()]

    @orm.db_session
    def get_by_id(self, recipe_id):
        r = Recipe[recipe_id]
        return r.to_dict()
