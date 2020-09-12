from datetime import datetime
from pony import orm


db = orm.Database()


class RecipeIndex(db.Entity):
    id = orm.PrimaryKey(int, auto=True)
    uid = orm.Required(str, unique=True, index=True)
    hash = orm.Required(str)
    last_update = orm.Required(datetime,
                               default=datetime.utcnow)
    recipe = orm.Optional('Recipe')


class Recipe(db.Entity):
    id = orm.PrimaryKey(RecipeIndex)
    data = orm.Required(orm.Json)
    name = orm.Required(str)
