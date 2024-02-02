from pathlib import Path

import yaml

folder = Path(__file__).parent

# Get a list of all 'index.md' files in subdirectories of the current directory
index_files = list(folder.glob("*/index.md"))
print(f"Found {len(index_files)} index files")
all_authors = []
# Iterate over the list of files
for file in index_files:
    with open(file, "r") as f:
        data = f.read()

    yaml_content = data.split("---")[1]
    yaml_data = yaml.safe_load(yaml_content)

    print(file.parent.name, yaml_data["authors"])
    all_authors.extend(yaml_data["authors"])

# Bin authors by first name
authors_by_first_name = {}
for author in all_authors:
    first_name = author.split(" ")[0]
    authors_by_first_name.setdefault(first_name, set()).add(author)
# Print the authors that have the same first name
for first_name, authors in authors_by_first_name.items():
    if len(authors) > 1:
        print(f"Authors with the same first name: {first_name}")
        for author in authors:
            print(f"  {author}")
        print()
