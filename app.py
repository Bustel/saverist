import os
import pathlib
import json
import pysolr

from flask import Flask, url_for, render_template, send_from_directory, request

SOLR_HOST = "http://localhost:8983/solr/saverist/"
archive_folder = "archive/"

app = Flask(__name__)
solr = pysolr.Solr(SOLR_HOST)

@app.route("/image/<pattern>/<fname>")
def image(pattern, fname):
    directory = pathlib.Path(archive_folder) / pattern / "images"
    return send_from_directory(directory, fname)


@app.route("/pdf/<pattern>/<fname>")
def pdf(pattern, fname):
    directory = pathlib.Path(archive_folder) / pattern / "pdfs"
    return send_from_directory(directory, fname)


@app.route("/zipfile/<pattern>/<fname>")
def zipfile(pattern, fname):
    directory = pathlib.Path(archive_folder) / pattern / "zips"
    return send_from_directory(directory, fname)



@app.route("/pattern/<pattern>")
def pattern(pattern):
    # TODO This seems very unsafe..
    with open(pathlib.Path(archive_folder) / pattern / "metadata.json", "r") as f:
        metadata = json.load(f)

    images = map(lambda img: url_for("image", pattern=pattern, fname=img["name"]), 
                 filter(lambda f: "thumbnail" not in f["name"],
                        metadata["gallery_links"]))

    pdfs = map(lambda f: (f["name"], url_for("pdf", pattern=pattern,
                                             fname=f["name"])), metadata["pdfs"])

    zips = map(lambda f: (f["name"], url_for("zipfile", pattern=pattern, fname=f["name"])), 
               metadata["zips"])

 
    return render_template("pattern.html", metadata=metadata, images=images,
                           pdfs=pdfs, zips=zips)


def get_all_ebooks():
    res = []
    archive = pathlib.Path(archive_folder)
    for path in os.listdir(archive):
        p = archive / pathlib.Path(path)
        if p.is_dir():
            res.append(path)
    return res

@app.route("/")
def index():
    pattern = get_all_ebooks()
    query = request.args.get("q")
    start = request.args.get("start", "0")
    rows = request.args.get("rows", "25") # TODO Fix this
    if query is None or query == "":
        query = "*:*"

    res = solr.search(q=query, start=start, rows=rows)

    return render_template("index.html", results=res)  

if __name__ == '__main__':
    app.run()
