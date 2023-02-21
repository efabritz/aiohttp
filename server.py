from sqlalchemy.exc import IntegrityError
from db import User, Advertisement, Session

import json
from aiohttp import web
from bcrypt import hashpw, gensalt, checkpw

from db import engine, Base



app = web.Application()


async def orm_context(app: web.Application):
    print("START")
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        # await conn.commit()
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    print("SHUTDOWN")

@web.middleware
async def session_middleware(requests: web.Request, handler):
    async with Session() as session:
        requests["session"] = session
        return await handler(requests)


app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)


def hash_password(password: str):
    password = password.encode()
    password = hashpw(password, salt=gensalt())
    return password.decode()


async def get_user(user_id: int, session: Session):
    user = await session.get(User, user_id)

    if user is None:
        raise web.HTTPNotFound(
            text=json.dumps({"status": "error", "message": "user not found"}),
            content_type="application/json",
        )

    return user

async def get_ad(ad_id: int, session: Session):
    ad = await session.get(Advertisement, ad_id)
    if ad is None:
        raise web.HTTPNotFound(
            text=json.dumps({"status": "error", "message": "ad not found"}),
            content_type="application/json",
        )
    return ad

class AdView(web.View):
    async def get(self):
        session = self.request['session']
        ad_id = int(self.request.match_info['ad_id'])
        ad = await get_ad(ad_id, session)
        return web.json_response({
            'id': ad.id,
            'header': ad.header,
            'description': ad.description,
            'creation_date': ad.creation_date.isoformat(),
            'author': ad.user_id
        })

    async def post(self):
        session = self.request['session']
        json_data = await self.request.json()
        ad = Advertisement(**json_data)
        session.add(ad)
        await session.commit()

        return web.json_response({
            'id': ad.id,
            'header': ad.header,
        })

    async def delete(self):
        ad_id = int(self.request.match_info["ad_id"])
        ad = await get_ad(ad_id, self.request["session"])
        await self.request["session"].delete(ad)
        await self.request["session"].commit()
        return web.json_response({"status": "success"})


    async def patch(self):
        ad_id = int(self.request.match_info["ad_id"])
        ad = await get_ad(ad_id, self.request["session"])
        json_data = await self.request.json()
        for key, value in json_data.items():
            setattr(ad, key, value)
        self.request["session"].add(ad)
        await self.request["session"].commit()
        return web.json_response({"status": "success"})

class UserView(web.View):
    async def get(self):
        session = self.request['session']
        user_id = int(self.request.match_info['user_id'])
        user = await get_user(user_id, session)
        return web.json_response({
                'id': user.id,
                'email': user.email,
                'username': user.username
        })

    async def post(self):
        session = self.request['session']
        json_data = await self.request.json()
        json_data['password'] = hash_password(json_data['password'])
        user = User(**json_data)
        session.add(user)
        try:
            await session.commit()
        except IntegrityError as error:
            raise  web.HTTPConflict(
                text=json.dumps({"status": "error", "message": "user already exists"}),
                content_type="application/json",
            )


        return web.json_response({
           'id': user.id,
            'username': user.username
        })

    async def patch(self):
        user_id = int(self.request.match_info["user_id"])
        user = await get_user(user_id, self.request["session"])
        json_data = await self.request.json()
        if "password" in json_data:
            json_data["password"] = hash_password(json_data["password"])
        for key, value in json_data.items():
            setattr(user, key, value)
        self.request["session"].add(user)
        await self.request["session"].commit()
        return web.json_response({"status": "success"})

    async def delete(self):
        user_id = int(self.request.match_info["user_id"])
        user = await get_user(user_id, self.request["session"])
        await self.request["session"].delete(user)
        await self.request["session"].commit()
        return web.json_response({"status": "success"})

app.add_routes(
    [
        web.get("/users/{user_id:\d+}/", UserView),
        web.post("/users/", UserView),
        web.patch("/users/{user_id:\d+}/", UserView),
        web.delete("/users/{user_id:\d+}/", UserView),
        web.get("/ads/{ad_id:\d+}/", AdView),
        web.post("/ads/", AdView),
        web.patch("/ads/{ad_id:\d+}/", AdView),
        web.delete("/ads/{ad_id:\d+}/", AdView),

    ]
)

web.run_app(app, port=8000)