import json
with open("brew.json", "r") as json_file:
    json_data = json.load(json_file)
cask_packages = []
packages = []
for category, apps in json_data.items():
    for app in apps:
        if app["cask"]:
            cask_packages.append(app["brew"])
        else:
            packages.append(app["brew"])
MULTILINE_BREAK = " \\\n  "
print(MULTILINE_BREAK.join(("brew install --cask", *sorted(cask_packages))))
print()
print(MULTILINE_BREAK.join(("brew install", *sorted(packages))))
