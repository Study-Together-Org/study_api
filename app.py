# from flask import Flask, abort, g, jsonify, request
import asyncio

from discord.ext import ipc
from quart import Quart, abort, jsonify, request

from common import async_utilities
from common.study import Study

app = Quart(__name__)


@app.before_first_request
async def create_db():
    """
    Initialize a study object and attach it to the quart app.
    - redis for connecting to redis
    - engine for connecting to sql
    - ipc_client for communicating with discord bot
    - ipc_lock for ensuring that only one request is made on ipc_client at a time
    """
    redis = await async_utilities.get_redis_pool()
    engine = await async_utilities.get_engine_pool()
    ipc_client = ipc.Client(secret_key="my_secret_key")
    ipc_lock = asyncio.Lock()
    app.study = Study(redis, engine, ipc_client, ipc_lock)  # type: ignore


@app.route("/userstats/<user_id>")
async def get_user_stats(user_id):
    """
    Return a user's study together stats.

    Parameters:
    - user_id (url param): the user's id
    """
    # abort_if_user_doesnt_exist(user_id)

    study = app.study  # type: ignore
    stats = await study.get_user_stats(user_id)
    roleInfo = await study.get_user_role_info(user_id)
    username = await study.get_username_from_user_id(user_id)
    return {"username": username, "stats": stats, "roleInfo": roleInfo}


@app.route("/usertimeseries/<user_id>")
async def get_user_timeseries(user_id):
    """
    Return a user's timeseries study data and neighbors.

    Parameters:
    - user_id (url param): the user's id
    - time_interval (query param): the time interval to query on
    """

    study = app.study  # type: ignore
    time_interval = request.args.get("time_interval")

    if not time_interval:
        abort(404)

    timeseries = await study.get_user_timeseries(user_id, time_interval)
    neighbors = await study.get_neighbor_stats(time_interval, user_id)
    return {"timeseries": timeseries, "neighbors": neighbors}


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
        limit = min(int(limit), 100)
    except:
        abort(404)

    if not time_interval:
        abort(404)

    leaderboard = await study.get_leaderboard(offset, limit, time_interval)
    return leaderboard


@app.route("/users")
async def username_lookup():
    """
    Return a list of users matching a prefix

    Parameters:
    - match (query param): the prefix to match
    """

    study = app.study  # type: ignore
    match = request.args.get("match")
    matching_users = await study.username_lookup(match)
    return jsonify(matching_users)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    app.run(loop=loop, debug=True)
