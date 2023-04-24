import json


def generate_markdown(json_data):
    def generate_app_section(app):
        maybe_cask = " --cask" if app["cask"] else ""
        base = (
            "https://formulae.brew.sh/cask/"
            if app["cask"]
            else "https://formulae.brew.sh/formula/"
        )
        lines = []
        brew_formula = base + app["brew"]
        if "/" not in app["brew"]:
            formula_line = f'[formula <em class="fas fa-flask fa-fw" style="margin-right: 0.2em;"> </em>]({brew_formula})'
            lines.append(formula_line)
        if repo := app.get("repo"):
            repo_line = f'[repo <em class="fab fa-github fa-fw" style="margin-right: 0.2em;"> </em>]({repo})'
            lines.append(repo_line)
        if docs := app.get("docs"):
            docs_line = f'[docs <em class="fas fa-book fa-fw" style="margin-right: 0.2em;"> </em>]({docs})'
            lines.append(docs_line)
        if lines:
            if len(lines) == 2:
                lines = [f"{lines[0]} and {lines[1]}"]
            elif len(lines) > 2:
                lines[-1] = f"and {lines[-1]}"
            references = f"* See the {', '.join(lines)}\n"

        return (
            f"#### {app['name']}\n"
            f"{app['description']}\n"
            f"* Install with `brew install{maybe_cask} {app['brew']}`\n"
            f"{references}\n"
        )

    return "\n".join(
        f"### {i}. {category}\n\n" + "".join(generate_app_section(app) for app in apps)
        for i, (category, apps) in enumerate(json_data.items(), start=1)
    )


with open("brew.json", "r") as json_file:
    json_data = json.load(json_file)

markdown = generate_markdown(json_data)
print(markdown)
