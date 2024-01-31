import yaml


def get_categories(path="categories.yaml"):
    with open(path) as file:
        code_categories = yaml.safe_load(file)
    name_categories = {v: k for k, v in code_categories.items()}
    return code_categories, name_categories

def lower_categories(categories):
    # map lowered keys to corresponding normal keys
    return {k.lower(): k for k, v in categories.items()}