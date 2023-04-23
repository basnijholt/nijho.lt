import json


def generate_markdown(json_data):
    markdown = ""
    for i, (category, apps) in enumerate(json_data.items(), start=1):
        markdown += f"### {i}. {category}\n\n"
        for app in apps:
            markdown += f"#### {app['name']}\n"
            markdown += f"{app['description']}\n"
            maybe_cask = " --cask" if app["cask"] else ""
            markdown += f"* Install with `brew install{maybe_cask} {app['brew']}`\n\n"
    return markdown


with open("brew.json", "r") as json_file:
    json_data = json.load(json_file)

markdown = generate_markdown(json_data)
print(markdown)
