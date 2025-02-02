import os
import pathlib
import json

from flask import Flask, url_for, render_template, send_from_directory

archive_folder = "archive/"

app = Flask(__name__)

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
    return render_template("index.html", pattern=pattern)  

if __name__ == '__main__':
    app.run()
