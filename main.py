import aiohttp
import asyncio
import bs4
import os
from pprint import pprint
from dataclasses import dataclass

@dataclass
class Ebook:
    title: str
    site_link: str
    product_image_url: str
    creator: str

# /users/login_signup
# head -> meta name:csrf-token
# _makerist_session

login_url = "https://www.makerist.de/users/login_signup"
login_url_post = "https://www.makerist.de/sessions"
ebook_url = "https://www.makerist.de/my/meine-anleitungen"

async def login(s: aiohttp.ClientSession, user: str, password: str):
    async with s.get(login_url) as rsp:
        html = await rsp.text()
        soup = bs4.BeautifulSoup(html, "html.parser")
        csrf_tag = soup.head.find_all("meta", attrs={"name":"csrf-token"})[0]
        csrf_token = csrf_tag.attrs["content"]

    for cookie in s.cookie_jar:
        pprint(cookie)

    login_data = {
        "authenticity_token": csrf_token,
        "session[email]": user,
        "session[password]": password,
        "session[remember_me]": "0",
        "commit": "Einloggen",
    }
    pprint(login_data)

    async with s.post(login_url_post, data=login_data) as rsp:
        html = await rsp.text()
        soup = bs4.BeautifulSoup(html, "html.parser")

    # TODO Verify login?

async def iter_ebooks(s: aiohttp.ClientSession):
    ebooks = []
    params = {"items": 12, "page": 1}

    while True:
        async with s.get(ebook_url, params=params) as rsp:
            html = await rsp.text()
            soup = bs4.BeautifulSoup(html, "html.parser")

            product_list = soup.find(id="my-products-list")

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
        await login(s, user, pw)
        
        async for ebook in iter_ebooks(s):
            print(ebook.title)
        
if __name__ == '__main__':
    asyncio.run(main())

