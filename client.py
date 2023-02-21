import asyncio
from aiohttp import ClientSession


async def main():

    async with ClientSession() as session:

        response = await session.post('http://127.0.0.1:8000/users/', json={'username':'user1', 'email':'user1@net.com', 'password':'1234'})

        #response = await session.get('http://127.0.0.1:8000/users/1/')

        #response = await session.post('http://127.0.0.1:8000/ads/', json={'header':'first_ad', 'description':'cgjdhgfkjkgjk', 'user_id': 1})

        #response = await session.get('http://127.0.0.1:8000/ads/1/')

        #response = await session.delete('http://127.0.0.1:8000/ads/6/')

        #response = await session.get('http://127.0.0.1:8000/ads/6/')

        print(response.status)
        print(await response.text())

asyncio.run(main())