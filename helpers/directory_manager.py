import os

DATA_PATH = "data"
INPUT_FORMS = os.path.join(DATA_PATH, "input_forms")
OUTPUT_BOMS = os.path.join(DATA_PATH, "output_boms")
OUTPUT_FORMS = os.path.join(DATA_PATH, "output_forms")
PROPEL_BOMS = os.path.join(DATA_PATH, "propel_boms")
SOLIDWORKS_BOMS = os.path.join(DATA_PATH, "solidworks_boms")
TEMPLATES = os.path.join(DATA_PATH, "templates")

DATA_DIRS = [
    DATA_PATH,
    OUTPUT_BOMS,
    OUTPUT_FORMS,
    PROPEL_BOMS,
    SOLIDWORKS_BOMS,
    TEMPLATES,
]


def makedirs():
    for dir in DATA_DIRS:
        if not os.path.isdir(dir):
            os.makedirs(dir)
