import json


def generate_markdown(json_data):
    markdown = ""
    for i, (category, apps) in enumerate(json_data.items(), start=1):
        markdown += f"### {i}. {category}\n\n"
        for app in apps:
            markdown += f"#### {app['name']}\n"
            markdown += f"{app['description']}\n"
            maybe_cask = " --cask" if app["cask"] else ""
            markdown += f"* Install with `brew install{maybe_cask} {app['brew']}`\n"
            repo = app.get("repo")
            docs = app.get("docs")
            if repo:
                fa = '<em class="fab fa-github fa-fw" style="margin-right: 0.2em;"> </em>'
                repo = f" [repo {fa}]({repo})"
            if docs:
                fa = '<em class="fas fa-book fa-fw" style="margin-right: 0.2em;"> </em>'
                docs = f" [docs {fa}]({docs})"
            if docs and repo:
                markdown += f"* See the {docs} and {repo}\n"
            elif docs:
                markdown += f"* See the {docs}\n"
            elif repo:
                markdown += f"* See the {repo}\n"
            markdown += "\n"
    return markdown


with open("brew.json", "r") as json_file:
    json_data = json.load(json_file)

markdown = generate_markdown(json_data)
print(markdown)
