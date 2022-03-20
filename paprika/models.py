from datetime import datetime
from pony import orm


db = orm.Database()


class RecipeIndex(db.Entity):
    id = orm.PrimaryKey(int, auto=True)
    uid = orm.Required(str, unique=True, index=True)
    hash = orm.Required(str)
    last_update = orm.Required(datetime, default=datetime.utcnow)
    recipe = orm.Optional("Recipe")


class Recipe(db.Entity):
    id = orm.PrimaryKey(RecipeIndex)
    name = orm.Required(str)
    data = orm.Required(orm.Json)


class Meal(db.Entity):
    id = orm.PrimaryKey(int, auto=True)
    uid = orm.Required(str)
    recipe_uid = orm.Required(str)
    recipe_name = orm.Required(str)
    meal_date = orm.Required(datetime)
    meal_order = orm.Required(int)
    meal_type = orm.Required(int)
