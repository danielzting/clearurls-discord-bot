import pathlib
import os.path


PATH_PACKAGE_DATA = os.path.join(pathlib.Path(__file__).parent.parent, "package_data")

PATH_RULESETS = (
    os.path.join(PATH_PACKAGE_DATA, "rulesets", "data.min.json"),
    os.path.join(PATH_PACKAGE_DATA, "rulesets", "unalix.json"),
    os.path.join(PATH_PACKAGE_DATA, "rulesets", "unalix_extended.json")
)
