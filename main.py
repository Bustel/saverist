import aiohttp
import asyncio
import bs4
import os
import json
import re
import pathlib
import getpass
from pprint import pprint
from dataclasses import dataclass, field, asdict

base_url = "https://www.makerist.de"
login_url = f"{base_url}/users/login_signup"
login_url_post = f"{base_url}/sessions"
ebook_url = f"{base_url}/my/meine-anleitungen"

content_str = "Beschreibung"
details_str = "Details"


def mostly_safe_path(dirty: str):
    clean =  re.sub(r"[/\\?%*:|\"<>\x7F\x00-\x1F]", "-", dirty) 
    return clean

async def download_file(session: aiohttp.ClientSession, url: str, dest: str):
    async with session.get(url) as rsp:
        with open(dest, "wb") as f:
            while chunk:= await rsp.content.read(1024):
                f.write(chunk)

@dataclass
class File:
    name: str
    link: str

@dataclass
class Ebook:
    title: str
    site_link: str
    product_image_url: str
    creator: str
    gallery_links: list[File] = field(default_factory=list)
    pdfs: list[File] = field(default_factory=list)
    zips: list[File] = field(default_factory=list)
    content_description: str | None = None
    product_details: str | None = None

    async def fetch_info(self, session: aiohttp.ClientSession):
        async with session.get(self.site_link) as rsp:
            html = await rsp.text()
            soup = bs4.BeautifulSoup(html, "html.parser")

            gallery = soup.find("div", class_="product-page__gallery-wrapper")
            if gallery is not None:
                for img in gallery.find_all("img"):
                    link = img.attrs["src"]
                    name = link.split("/")[-1]
                    self.gallery_links.append(File(name=name,link=link))

            for button in soup.find_all(id="download-pattern-zip-button"):
                name = button.attrs["download"]
                link = base_url + button.attrs["href"]
                self.zips.append(File(name=name, link=link))

            for div in soup.find_all("div", class_="pdf-download-link"):
                for a in div.find_all("a"):
                    link = base_url + a.attrs["href"]
                    name = a.attrs["href"].split("/")[-2] + ".pdf"
                    self.pdfs.append(File(name=name, link=link))

            content = soup.find_all("div", class_="product-page__accordion-content")
            for part in content:
                if part.previous_sibling.get_text() == content_str:
                    self.content_description = part.get_text()                    

                if part.previous_sibling.get_text() == details_str:
                    self.product_details = part.get_text()                    

    def to_json(self):
        return json.dumps(asdict(self), indent=4)

    async def archive(self, session: aiohttp.ClientSession, dest: str):
        dest_path = pathlib.Path(dest)
        folder = dest_path / mostly_safe_path(self.title) 
        folder.mkdir()

        with open(folder / "metadata.json", "w") as f:
            f.write(self.to_json())

        tasks = []

        images_dest = folder / "images"
        images_dest.mkdir()
        for img in self.gallery_links:
            tasks.append(download_file(session, img.link, images_dest / img.name))

        pdf_dest = folder / "pdfs"
        pdf_dest.mkdir()
        for pdf in self.pdfs:
            tasks.append(download_file(session, pdf.link, pdf_dest / pdf.name))

        zip_dest = folder / "zips"
        zip_dest.mkdir()
        for z in self.zips:
            tasks.append(download_file(session, z.link, zip_dest / z.name))

        await asyncio.gather(*tasks)


# /users/login_signup
# head -> meta name:csrf-token
# _makerist_session
async def login(s: aiohttp.ClientSession, user: str, password: str):
    async with s.get(login_url) as rsp:
        html = await rsp.text()
        soup = bs4.BeautifulSoup(html, "html.parser")
        csrf_tag = soup.head.find_all("meta", attrs={"name":"csrf-token"})[0]
        csrf_token = csrf_tag.attrs["content"]

    # for cookie in s.cookie_jar:
    #     pprint(cookie)

    login_data = {
        "authenticity_token": csrf_token,
        "session[email]": user,
        "session[password]": password,
        "session[remember_me]": "0",
        "commit": "Einloggen",
    }
    # pprint(login_data)

    async with s.post(login_url_post, data=login_data) as rsp:
        html = await rsp.text()
        soup = bs4.BeautifulSoup(html, "html.parser")
        # print(soup.prettify())

    # TODO Verify login?


async def iter_ebooks(s: aiohttp.ClientSession):
    ebooks = []
    params = {"items": 12, "page": 1}

    while True:
        async with s.get(ebook_url, params=params) as rsp:
            html = await rsp.text()
            soup = bs4.BeautifulSoup(html, "html.parser")

            product_list = soup.find(id="my-products-list")

            if product_list is None:
                print("Keine E-Books gefunden. Ist der Login korrekt?")
                return

            for product in product_list.find_all("div", class_="product"):
                title = product.find("div", class_="product__title").get_text()
                link = product.find("div",class_="product__title").find("a").attrs["href"]
                creator = product.find("div", class_="product__creator").get_text() 
                product_image_url = product.find("img").attrs["src"]

                ebook = Ebook(title=title, site_link=link,
                              product_image_url=product_image_url,
                              creator=creator)

                yield ebook


            nextPage = product_list.find("a", rel="next")
            if nextPage is None:
                break
            else:
                params["page"] += 1


async def main():
    async with aiohttp.ClientSession() as s:
        user =  os.getenv("MAKERIST_USERNAME")
        pw = os.getenv("MAKERIST_PASSWORD")

        if user is None:
            user = input("Benutzername/E-Mail:").strip()

        if pw is None:
            pw = getpass.getpass("Passwort:")

        await login(s, user, pw)
        
        archive = pathlib.Path("archive")
        archive.mkdir(exist_ok=True)
        count = 1
        archived = 0
        skipped = 0
        async for ebook in iter_ebooks(s):
            await ebook.fetch_info(s)
            try: 
                await ebook.archive(s, archive)
                print(f"[{count}] -- {ebook.title} archiviert.")
                archived += 1
            except FileExistsError:
                print(f"[{count}] -- Überspringe {ebook.title}. Existiert bereits.")
                skipped += 1

            count += 1

        print("===== ARCHIVIERUNG ABGESCHLOSSEN ====")
        print(f"{archived} Ebooks archiviert. {skipped} übersprungen.")
        
if __name__ == '__main__':
    asyncio.run(main())

