import sys
from urllib.request import Request, urlopen

import pandas as pd
import toml
from bs4 import BeautifulSoup
from schema import Schema, Or, And, Use
from tqdm import tqdm

try:
    config = toml.load("config.toml")
except FileNotFoundError:
    print(
        "No config file found. "
        "Please define a config.toml as per the config.example.toml file."
    )
    sys.exit()

# Config Schema Definition
config_schema = Schema(
    {
        "bot": {
            "tag": str,
            "pages": int,
            "top_positional_tags": Or(True, False),
            "tpt_limit": And(Use(int), lambda n: n > 0),
            "csv": Or(True, False),
            "debug": Or(True, False),
        }
    },
    ignore_extra_keys=True,
)
config_schema.validate(config)

# Configurations
tag = config['bot']['tag']
pages = config['bot']['pages']
top_positional_tags = config['bot']['top_positional_tags']
tpt_limit = config['bot']['tpt_limit']
csv = config['bot']['csv']
debug = config['bot']['debug']

# Constants
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Variables
servers = []

# Progress Bar
print(f"Fetching {pages} Pages: \n")
if not debug:
    bar = tqdm(total=pages)

# Iterate over each page for a tag
for page in range(1, pages + 1):
    url = f"https://disboard.org/servers/tag/{tag}/{page}?sort=-member_count"
    request = Request(url, headers=HEADERS)
    resource = urlopen(request)
    content = resource.read().decode(resource.headers.get_content_charset())
    soup = BeautifulSoup(content, 'html.parser')

    # Iterate over each server
    for server_info in soup.find_all(class_='server-info'):
        server_name = server_info.find(class_="server-name")
        server_name_link = server_name.find('a')
        server_online = server_info.find(class_="server-online")

        parent = server_info.parent.parent
        tags = []
        for tag_ in parent.find_all(class_="tag"):
            tag_name = tag_.find(class_="name")
            tags.append(tag_name.contents[0].strip())

        # Check servers without online counts
        if hasattr(server_online, 'contents'):
            members_online_count = server_online.contents[0].strip()
        else:
            members_online_count = "N/A"

        # Create a server
        server = [
            server_name_link.contents[0].strip(),
            members_online_count
        ]
        server.extend(tags)

        if debug:
            print(f"Server: {server}")

        # Add each server found
        servers.append(server)

    # Increment Progress
    if not debug:
        bar.update(1)

df = pd.DataFrame(
    servers,
    columns=[
        'Server Name',
        'Members Online',
        'Tag 1',
        'Tag 2',
        'Tag 3',
        'Tag 4',
        'Tag 5'
    ]
)

# Close Progress Bar
if not debug:
    bar.close()

if top_positional_tags:
    print("\n== Top Tags by Position ==")
    for i in range(1, 6):
        print(f"Tag {i}: ")
        print(f"{str(df[f'Tag {i}'].value_counts()[:tpt_limit])}\n")

if csv:
    print("Creating output file...")
    df.to_csv(f'{tag}_servers.csv', index=False, encoding='utf-8-sig')
    print(f"Done writing: {tag}_servers.csv")
else:
    print("Exiting without writing file!")
