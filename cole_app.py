import asyncio
import uvloop
import logging
import os
import ssl

import discord
from dotenv import load_dotenv
from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart, abort, jsonify, request, redirect
from quart_cors import cors
from quart_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

from cole_bot import MyBot
from common import async_utilities
from common.study import Study
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# ipclogger = logging.getLogger('discord.ext.ipc.client')
# ipclogger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='ipc_client.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# ipclogger.addHandler(handler)

discordlogger = logging.getLogger('discord')
discordlogger.setLevel(logging.WARN)
handler = logging.FileHandler(filename='discord_bot.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
discordlogger.addHandler(handler)

load_dotenv("dev.env")

app = Quart(__name__)
app = cors(app, allow_origin=["http://localhost:3000", "http://localhost:5000", "https://app.studytogether.com",
    "https://studytogether.com", "https://www.studytogether.com", "https://app.dev.studytogether.com"], allow_credentials=True)

app.secret_key = bytes(os.getenv("APP_SECRET_KEY"), encoding="ascii")
app.config["DISCORD_CLIENT_ID"] = os.getenv("DISCORD_CLIENT_ID")  # Discord client ID.
app.config["DISCORD_CLIENT_SECRET"] = os.getenv("DISCORD_CLIENT_SECRET")  # Discord client secret.
app.config["DISCORD_REDIRECT_URI"] = os.getenv("DISCORD_REDIRECT_URI")  # URL to your callback endpoint.

debug_mode = True if os.getenv("DEBUG_MODE") == "true" else False

discord_oauth = DiscordOAuth2Session(app)

time_intervals = ("pastDay", "pastWeek", "pastMonth", "allTime")


async def abort_if_invalid_time_interval(time_interval):
    if time_interval not in time_intervals:
        abort(404)


async def abort_if_user_doesnt_exist(user_id):
    study = app.study  # type: ignore
    if not await study.user_exists(user_id):
        abort(404)


@app.before_serving
async def initialize_app_study():
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    """
    Initialize a study object and attach it to the quart app.
    - redis for connecting to redis
    - engine for connecting to sql
    - my_bot for interacting with discord things
    """
    redis = await async_utilities.get_redis_pool()
    engine = await async_utilities.get_engine_pool()
    # bot = ipc.Client(secret_key="my_secret_key", port=8765)
    my_bot = MyBot(command_prefix="random_word", intents=discord.Intents.all())
    loop.create_task(my_bot.start(os.getenv("bot_token")))
    print("Starting bot")
    await my_bot.wait_until_ready()
    app.study = Study(redis, engine, my_bot)  # type: ignore
    print("Initialized app study complete")


@app.after_serving
async def shutdown_connections():
    # close redis pool
    app.study.redis_client.close()
    await app.study.redis_client.wait_closed()

    # close engine
    await app.study.engine.dispose()


@app.route("/login/")
async def login():
    return await discord_oauth.create_session()


@app.route("/logout/")
@requires_authorization
async def logout():
    discord_oauth.revoke()
    return "Logout complete"


@app.route("/callback/")
async def callback():
    # saves everything in session
    print("Saving to session")
    await discord_oauth.callback()
    return redirect("http://localhost:3000/")
    # return redirect(url_for(".me"))


@app.errorhandler(Unauthorized)
async def redirect_unauthorized(e):
    abort(404)
    # return "Unauthorized"
    # return redirect(url_for("login"))


# @requires_authorization
@app.route("/me")
async def me():
    valid = await discord_oauth.authorized

    if valid:
        user = await discord_oauth.fetch_user()
        # print(user)
        return {
            "id": str(user.id),
            "username": user.username,
            "discriminator": user.discriminator,
            "avatar_url": user.avatar_url,
            "email": user.email
        }
    else:
        abort(404)
        # return "Not authorized"


# @requires_authorization
@app.route("/userstats/<user_id>")
async def get_user_stats(user_id):
    """
    Return a user's study together stats.

    Parameters:
    - user_id (url param): the user's id
    """
    await abort_if_user_doesnt_exist(user_id)

    study = app.study  # type: ignore
    stats = await study.get_user_stats(user_id)
    roleInfo = await study.get_user_role_info(user_id)
    username = await study.get_username_from_user_id(user_id)
    return {"username": username, "stats": stats, "roleInfo": roleInfo}


# @requires_authorization
@app.route("/usertimeseries/<user_id>")
async def get_user_timeseries(user_id):
    """
    Return a user's timeseries study data and neighbors.

    Parameters:
    - user_id (url param): the user's id
    - time_interval (query param): the time interval to query on
    """
    time_interval = request.args.get("time_interval")

    await abort_if_user_doesnt_exist(user_id)
    await abort_if_invalid_time_interval(time_interval)

    study = app.study  # type: ignore

    timeseries = await study.get_user_timeseries(user_id, time_interval)
    neighbors = await study.get_neighbor_stats(time_interval, user_id)
    return {"timeseries": timeseries, "neighbors": neighbors}


# @requires_authorization
@app.route("/leaderboard")
async def get_leaderboard():
    """
    Return a study hours leaderboard

    Parameters:
    - offset (query param): the offset to query from
    - limit (query param): the number of users to query
    - time_interval (query param): the time interval to query on

    """
    study = app.study  # type: ignore
    offset = request.args.get("offset")
    limit = request.args.get("limit")
    time_interval = request.args.get("time_interval")

    try:
        offset = int(offset)
        limit = min(int(limit), 500)
    except:
        abort(404)

    await abort_if_invalid_time_interval(time_interval)

    leaderboard = await study.get_leaderboard(offset, limit, time_interval)
    return leaderboard


# @requires_authorization
@app.route("/users")
async def username_lookup():
    """
    Return a list of users matching a prefix

    Parameters:
    - match (query param): the prefix to match
    """
    match = request.args.get("match")

    # abort if no match parameter
    if match is None:
        abort(404)

    study = app.study  # type: ignore
    matching_users = await study.username_lookup(match)
    return jsonify(matching_users)


def _exception_handler(loop: asyncio.AbstractEventLoop, context: dict) -> None:
    exception = context.get("exception")
    if isinstance(exception, ssl.SSLError):
        pass  # Handshake failure
    else:
        loop.default_exception_handler(context)


# doesn't get run with hypercorn
if __name__ == "__main__":
    if os.getenv("MODE") == "production":
        config = Config()
        config.certfile = os.getenv("CERTFILE")
        config.keyfile = os.getenv("KEYFILE")
        config.bind = [os.getenv("BIND")]
        config.accesslog = "api_access.log"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.set_debug(debug_mode)
        loop.set_exception_handler(_exception_handler)
        loop.run_until_complete(serve(app, config))
    else:
        app.run(host="0.0.0.0", debug=debug_mode)
