"""Generate advent calendar blog posts from YAML configuration."""
from pathlib import Path
import time
from typing import Optional
from urllib.parse import urlparse

import httpx
import yaml
from jinja2 import Environment, FileSystemLoader

# Templates same as before
INTRO_TEMPLATE = """# {{ title }}

{{ content }}
"""

POST_TEMPLATE = """# Day {{ day }}: {{ title }} {{ emoji }}

{{ tagline }}

{{ description }}

{% if type == "combined" %}
This post combines several related projects:

{% for repo in constituent_repos %}
* [{{ repo.name }}]({{ repo.url }}) - {{ repo.description }} {% if repo.stars %}({{ repo.stars }} ⭐){% endif %}
{% endfor %}
{% else %}
## Project Overview
* GitHub: [{{ repo }}]({{ url }})
* Stars: {{ stars }} ⭐
* License: {{ license }}
{% endif %}

{% if origin_story %}
## Origin Story
{{ origin_story }}
{% endif %}

{% if technical_highlights %}
## Technical Highlights
{{ technical_highlights }}
{% endif %}

{% if impact %}
## Impact
{% if type == "combined" %}
Total stars: {{ impact.total_stars }}
{% else %}
* GitHub stars: {{ impact.stars }}
* Active users: {{ impact.users }}
{% endif %}
{% endif %}

{% if challenges %}
## Challenges and Solutions
{{ challenges }}
{% endif %}

{% if lessons_learned %}
## Lessons Learned
{{ lessons_learned }}
{% endif %}

{% if future_plans %}
## Future Plans
{{ future_plans }}
{% endif %}

## Technologies Used
{% for tech in technologies %}
* {{ tech }}
{% endfor %}
"""

def get_github_repo_info(url: str, client: httpx.Client) -> Optional[dict]:
    """Get repository information from GitHub API."""
    try:
        # Extract owner and repo from URL
        path = urlparse(url).path.strip("/")
        owner, repo = path.split("/")[:2]
        
        # Make API request
        response = client.get(f"https://api.github.com/repos/{owner}/{repo}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching info for {url}: {e}")
        return None

def update_project_with_github_info(project: dict, client: httpx.Client) -> dict:
    """Update project data with GitHub information."""
    if project.get("type") == "combined":
        # Handle combined projects
        total_stars = 0
        for repo in project["constituent_repos"]:
            if "url" in repo and "github.com" in repo["url"]:
                info = get_github_repo_info(repo["url"], client)
                if info:
                    repo["stars"] = info["stargazers_count"]
                    total_stars += info["stargazers_count"]
                time.sleep(0.5)  # Be nice to GitHub API
        project["impact"]["total_stars"] = total_stars
    else:
        # Handle single projects
        if "url" in project and "github.com" in project["url"]:
            info = get_github_repo_info(project["url"], client)
            if info:
                project["stars"] = info["stargazers_count"]
                if "impact" not in project:
                    project["impact"] = {}
                project["impact"]["stars"] = info["stargazers_count"]
    return project

def load_config(path: str = "advent_posts.yaml") -> dict:
    """Load YAML configuration file."""
    with open(path) as f:
        return yaml.safe_load(f)

def create_post(template: str, data: dict, day: int, output_dir: Path) -> None:
    """Create a single blog post from template and data."""
    env = Environment(loader=FileSystemLoader("."))
    template = env.from_string(template)
    
    # Add day number to data
    post_data = {**data, "day": day}
    content = template.render(**post_data)
    
    # Create filename based on day number or special name for intro
    filename = f"day_{day:02d}.md"
    output_path = output_dir / filename
    output_path.write_text(content)
    print(f"Created {output_path}")

def main():
    """Generate all blog posts."""
    config = load_config()
    output_dir = Path("generated_posts")
    output_dir.mkdir(exist_ok=True)
    
    # Create introduction
    create_post(INTRO_TEMPLATE, config["introduction"], 0, output_dir)
    
    # Set up GitHub API client
    token = Path(".github_token").read_text().strip()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    with httpx.Client(headers=headers) as client:
        # Create individual posts
        for i, post in enumerate(config["projects"], start=1):
            if i <= 24:  # Only process first 24 projects
                post = update_project_with_github_info(post, client)
                create_post(POST_TEMPLATE, post, i, output_dir)

if __name__ == "__main__":
    main()