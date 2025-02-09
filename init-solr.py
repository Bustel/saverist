import aiohttp
import asyncio
import pysolr
import pathlib
import json
import os

SOLR_HOST = "http://localhost:8983"
archive_folder = "archive/"


payload = { 
    "add-field": [
    {
        "name": "title",
        "type": "text_general",
        "stored": "true",
        "multiValued": "false",
    },
    {
        "name": "path",
        "type": "text_general",
        "stored": "true",
        "multiValued": "false",
    },
    {
        "name": "content-description",
        "type": "text_general",
        "stored": "true",
    },
    {
        "name": "creator",
        "type": "text_general",
        "stored": "true",
        "multiValued": "false",
    },
    {
        "name": "thumbnail",
        "type": "text_general",
        "stored": "true",
        "indexed": "false",
        "multiValued": "false",
    },
    {
        "name": "_creator_",
        "type": "string",
        "stored": "true",
        "indexed": "false",
        "multiValued": "false",
        "docValues": "true"
    },
    ],
    "add-copy-field": [
        {
        "source": "*",
        "dest": "_text_"
        },
        {
        "source": "creator",
        "dest": "_creator_",
        }
    ]
}

def get_all_ebooks():
    res = []
    archive = pathlib.Path(archive_folder)
    for path in os.listdir(archive):
        p = archive / pathlib.Path(path)
        if p.is_dir():
            res.append(path)
    return res



async def create_schema():
    async with aiohttp.ClientSession() as s:
        async with s.post(f"{SOLR_HOST}/solr/saverist/schema", json=payload) as rsp:
            print(await rsp.json())

def add_ebooks():
    solr = pysolr.Solr(f"{SOLR_HOST}/solr/saverist", always_commit=True)
    solr.ping()

    docs = []
    for p in get_all_ebooks():
        path = pathlib.Path(archive_folder) / p
        with open(path / "metadata.json", "r") as f:
            metadata = json.load(f)
            doc = {
                   "title": metadata["title"], 
                   "path": p,
                   "creator": metadata["creator"],
                   "content-description": metadata["content_description"]
                  }

            for l in metadata["gallery_links"]:
                if "featured" in l["name"] and "thumbnail" in l["name"]:
                    doc["thumbnail"] = l["name"]
                    break
            docs.append(doc)
    solr.add(docs)


if __name__ == '__main__':
    asyncio.run(create_schema())
    add_ebooks()

