import aiohttp
import asyncio
import os

# /users/login_signup
# head -> meta name:csrf-token
# _makerist_session

PASSWORD = os.getenv("PASSWORD")
USERNAME = os.getenv("USERNAME")

async def main():
    with aiohttp.ClientSession() as s:
        async with s.get(


if __name__ == '__main__':
    asyncio.run(main())

