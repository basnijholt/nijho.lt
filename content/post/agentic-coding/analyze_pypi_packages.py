#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["requests", "matplotlib", "seaborn"]
# ///
"""Analyze PyPI package publication dates and create histograms."""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import seaborn as sns
import requests

# Set the style for better-looking plots
sns.set_style("whitegrid")
sns.set_palette("husl")


def get_user_packages(username: str) -> List[str]:
    """Get all packages for a PyPI user."""
    # First, let's try to get packages by searching for the author
    packages = []

    # We'll need to search for packages - PyPI doesn't have a direct "list by owner" API
    # So we'll need to know the package names. Let's start with a manual list
    # that we can expand

    # Packages from basnijholt's PyPI account
    known_packages = [
        "matty",
        "markdown-code-runner",
        "slurm-usage",
        "agent-cli",
        "unidep",
        "wenfire",
        "mindroom",
        "home-assistant-streamdeck-yaml",
        "pixi-to-conda-lock",
        "pipefunc",
        "adaptive-scheduler",
        "gh-download",
        "graphviz-anywidget",
        "numthreads",
        "adaptive",
        "dotbins",
        "calver-auto-release",
        "clip-files",
        "rsync-time-machine",
        "tuitorial",
        "opennb",
        "fileup",
        "pfapack",
        "yaml2bib",
        "dotenvx",
        "conda-join",
        "azure-quantum-tgp",
        "codestructure",
        "miflora",
        "aiokef",
        "hpc05",
        "text-histogram3",
    ]

    # Check which packages actually exist
    for package in known_packages:
        url = f"https://pypi.org/pypi/{package}/json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            packages.append(package)
            print(f"✓ Found package: {package}")
        elif response.status_code == 404:
            print(f"✗ Package not found: {package}")
        else:
            print(f"⚠ Error fetching {package}: HTTP {response.status_code}")

    return packages


def get_package_info(package_name: str) -> Tuple[str, Dict]:
    """Get package information from PyPI."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return package_name, response.json()


def parse_release_dates(package_data: Dict) -> Dict[str, List[datetime]]:
    """Parse release dates from package data."""
    releases = {}

    if "releases" in package_data:
        for version, release_info in package_data["releases"].items():
            if release_info:  # Some versions might have empty data
                # Get the upload time of the first file in this release
                upload_time = release_info[0].get("upload_time_iso_8601")
                if upload_time:
                    dt = datetime.fromisoformat(upload_time.replace("Z", "+00:00"))
                    releases[version] = dt

    return releases


def analyze_packages(
    username: str = "basnijholt",
) -> Tuple[Dict[int, int], Dict[int, int]]:
    """Analyze all packages for a user and return publication stats."""
    packages = get_user_packages(username)
    print(f"\nFound {len(packages)} packages for {username}\n")

    initial_publications = defaultdict(int)  # Year -> count of first releases
    all_releases = defaultdict(int)  # Year -> count of all releases

    for package_name in packages:
        _, package_data = get_package_info(package_name)

        if package_data:
            releases = parse_release_dates(package_data)

            if releases:
                # Get all release dates
                all_dates = sorted(releases.values())

                # First release
                if all_dates:
                    first_release = all_dates[0]
                    initial_publications[first_release.year] += 1

                    # All releases
                    for dt in all_dates:
                        all_releases[dt.year] += 1

                    print(
                        f"{package_name}: First release {first_release.year}, Total releases: {len(all_dates)}"
                    )

    return dict(initial_publications), dict(all_releases)


def create_histograms(initial_pubs: Dict[int, int], all_rels: Dict[int, int]):
    """Create histograms for package publications."""
    # Calculate total packages for subtitle
    total_packages = sum(initial_pubs.values())
    total_releases = sum(all_rels.values())

    # Use built-in dark theme
    plt.style.use("dark_background")

    # Create figure with size appropriate for web/blog use
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Get the full range of years for consistent x-axis
    all_years = sorted(set(initial_pubs.keys()) | set(all_rels.keys()))
    year_range = range(min(all_years), max(all_years) + 1)

    # Initial publications histogram
    if initial_pubs:
        # Fill in missing years with 0
        years1 = list(year_range)
        counts1 = [initial_pubs.get(year, 0) for year in years1]

        ax1.bar(years1, counts1, color="#4ECDC4", edgecolor="#7EFFF7", linewidth=1)
        ax1.set_xlabel("Year", fontsize=12, fontweight="bold")
        ax1.set_ylabel("Number of Packages", fontsize=12, fontweight="bold")
        ax1.set_title(
            "Initial Package Publications", fontsize=14, fontweight="bold", pad=15
        )

        # Add value labels on bars (only for non-zero values)
        for year, count in zip(years1, counts1):
            if count > 0:
                ax1.text(
                    year,
                    count + 0.1,
                    str(count),
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                    color="#7EFFF7",
                )

        # Force all years to show on x-axis
        ax1.set_xticks(years1)
        ax1.set_xticklabels(years1, rotation=45, ha="right")

        # Set integer y-axis
        ax1.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

        # Minimal styling - only horizontal grid lines
        ax1.grid(axis="y", alpha=0.2, linestyle=":")
        ax1.grid(axis="x", visible=False)  # Disable vertical grid lines
        ax1.set_axisbelow(True)

    # All releases histogram
    if all_rels:
        # Fill in missing years with 0
        years2 = list(year_range)
        counts2 = [all_rels.get(year, 0) for year in years2]

        ax2.bar(years2, counts2, color="#FF6B6B", edgecolor="#FFB4B4", linewidth=1)
        ax2.set_xlabel("Year", fontsize=12, fontweight="bold")
        ax2.set_ylabel("Number of Releases", fontsize=12, fontweight="bold")
        ax2.set_title("All Package Releases", fontsize=14, fontweight="bold", pad=15)

        # Add value labels on bars (only for non-zero values)
        for year, count in zip(years2, counts2):
            if count > 0:
                ax2.text(
                    year,
                    count + 1,
                    str(count),
                    ha="center",
                    va="bottom",
                    fontsize=10,
                    fontweight="bold",
                    color="#FFB4B4",
                )

        # Force all years to show on x-axis
        ax2.set_xticks(years2)
        ax2.set_xticklabels(years2, rotation=45, ha="right")

        # Set integer y-axis
        ax2.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

        # Minimal styling - only horizontal grid lines
        ax2.grid(axis="y", alpha=0.2, linestyle=":")
        ax2.grid(axis="x", visible=False)  # Disable vertical grid lines
        ax2.set_axisbelow(True)

    # Add main title and subtitle
    fig.suptitle(
        "PyPI Package Publication Analysis", fontsize=18, fontweight="bold", y=1.05
    )

    # Add subtitle with total package count
    fig.text(
        0.5,
        0.98,
        f"Total: {total_packages} packages • {total_releases} releases",
        ha="center",
        fontsize=13,
        color="#a0a0a0",
    )

    plt.tight_layout()

    # Save the figure in both PNG and SVG formats
    output_file_png = "pypi_packages_histogram.png"
    output_file_svg = "pypi_packages_histogram.svg"

    # Save PNG with good resolution
    plt.savefig(output_file_png, dpi=150, bbox_inches="tight")

    # Save SVG (figsize already controls the size)
    plt.savefig(output_file_svg, format="svg", bbox_inches="tight")

    print(f"\nHistogram saved as '{output_file_png}' and '{output_file_svg}'")

    plt.show()


def main():
    """Main function."""
    print("Analyzing PyPI packages...")
    print("=" * 50)

    # You can change the username here
    username = "basnijholt"

    initial_pubs, all_releases = analyze_packages(username)

    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Total unique packages: {sum(initial_pubs.values())}")
    print(f"Total releases across all packages: {sum(all_releases.values())}")
    print(
        f"Years active: {min(initial_pubs.keys()) if initial_pubs else 'N/A'} - {max(all_releases.keys()) if all_releases else 'N/A'}"
    )

    # Create visualizations
    create_histograms(initial_pubs, all_releases)


if __name__ == "__main__":
    main()
