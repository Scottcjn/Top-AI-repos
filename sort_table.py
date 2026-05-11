import re
import requests
import os
import time

def get_github_stars(repo_slug):
    """Fetches the star count for a given GitHub repository slug."""
    api_url = f"https://api.github.com/repos/{repo_slug}"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        return data.get("stargazers_count", 0)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching stars for {repo_slug}: {e}")
        return -1  # Return -1 to indicate an error, will be sorted to the bottom

def sort_markdown_table(markdown_content):
    lines = markdown_content.splitlines()
    header_index = None

    for index, line in enumerate(lines):
        if re.match(r'^\s*\|.*<ins>#</ins>.*\|\s*$', line):
            header_index = index
            break

    if header_index is None:
        print("Table header or separator not found.")
        return markdown_content

    separator_index = header_index + 1
    if separator_index >= len(lines):
        print("Table header or separator not found.")
        return markdown_content

    separator_line = lines[separator_index]
    separator_pattern = r'^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$'
    if not re.match(separator_pattern, separator_line):
        print("Table header or separator not found.")
        return markdown_content

    table_body_end_index = len(lines)
    for index in range(separator_index + 1, len(lines)):
        if lines[index].startswith("##"):
            table_body_end_index = index
            break

    content_before_table = "\n".join(lines[:header_index])
    content_after_table = "\n".join(lines[table_body_end_index:])

    original_header_line = lines[header_index]
    original_separator_line = separator_line

    # Extract table body rows
    rows = lines[separator_index + 1:table_body_end_index]
    
    parsed_repos = []

    # Regex to extract repo slug from the Repo_Stars column's img src
    repo_slug_regex = re.compile(r'src="https://custom-icon-badges.herokuapp.com/github/stars/([^/]+/[^?]+)\?')

    for i, row in enumerate(rows):
        if not row.strip():
            continue

        cols = row.split('|')
        if len(cols) < 7:
            print(f"Skipping malformed row (not enough columns): {row}")
            continue

        repo_stars_column_content = cols[3] # This is the content of the Repo_Stars column

        repo_slug = None
        slug_match = repo_slug_regex.search(repo_stars_column_content)
        if slug_match:
            repo_slug = slug_match.group(1)
        else:
            # Fallback: try to get from the main repo link in the second column (cols[2])
            repo_link_match = re.search(r'\[.*?\]\((https://github.com/([^/]+/[^)]+))\)', cols[2])
            if repo_link_match:
                repo_slug = repo_link_match.group(2)

        stars = 0
        if repo_slug:
            stars = get_github_stars(repo_slug)
            print(f"Fetched stars for {repo_slug}: {stars}")
            time.sleep(0.1) # Be kind to the API, 60 requests/hour limit
        else:
            print(f"Could not extract repo slug from row: {row}")

        parsed_repos.append({'original_row': row, 'stars': stars, 'repo_slug': repo_slug})

    # Sort by stars in descending order
    parsed_repos.sort(key=lambda x: x['stars'], reverse=True)

    # Reconstruct the table body with updated numbering
    sorted_rows = []
    for i, repo_data in enumerate(parsed_repos):
        original_row = repo_data['original_row']
        cols = original_row.split('|')
        if len(cols) > 1:
            cols[1] = str(i + 1) # Update the number
            sorted_rows.append('|'.join(cols))
        else:
            sorted_rows.append(original_row)

    new_table_body = "\n".join(sorted_rows)
    
    # Construct the new full table block
    new_full_table_block = original_header_line + "\n" + original_separator_line + "\n" + new_table_body + "\n"

    # Construct the full new markdown content
    parts = []
    if content_before_table:
        parts.append(content_before_table)
    parts.append(new_full_table_block.rstrip("\n"))
    if content_after_table:
        parts.append(content_after_table)
    new_markdown_content = "\n".join(parts)

    return new_markdown_content

DEFAULT_FILE_PATH = r"C:\Users\ishan\Documents\Projects\Top-AI-repos\README.md"


def main(file_path=DEFAULT_FILE_PATH):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    updated_content = sort_markdown_table(content)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print("Table sorting complete. Check README.md")


if __name__ == "__main__":
    main()
