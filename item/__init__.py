from .categories import get_categories, lower_categories

CODE_CATEGORIES, NAME_CATEGORIES = get_categories()
CODE_CATEGORIES_LOWER = lower_categories(CODE_CATEGORIES)
NAME_CATEGORIES_LOWER = lower_categories(NAME_CATEGORIES)
