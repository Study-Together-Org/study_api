# from flask import Flask, abort, g, jsonify, request
import asyncio
import os

from discord.ext import ipc
from dotenv import load_dotenv
from quart import Quart, abort, g, jsonify, request

from common.study import Study

app = Quart(__name__)
ipc_client = ipc.Client(secret_key="my_secret_key")
load_dotenv("dev.env")


# args_parser.add_argument("offset", type=int)
# args_parser.add_argument("limit", type=int)
# args_parser.add_argument("time_interval", type=str)
# args_parser.add_argument("match", type=str)

# study = Study()

# def abort_if_user_doesnt_exist(discord_user_id):
#     if not study.user_exists(discord_user_id):
#         abort(404, message="User {} doesn't exist".format(discord_user_id))
study = None


async def connect_study():
    return await Study.create()


async def get_study():
    if not hasattr(g, "study"):
        # start thread for discord bot
        g.study = await connect_study()
    return g.study
# 
# 
# @app.teardown_appcontext
# def close_study(e):
#     if hasattr(g, "study"):
#         g.study.close()


@app.route("/userstats/<user_id>")
async def get_user_stats(user_id):
    # abort_if_user_doesnt_exist(user_id)
    # study = Study()
    study = await get_study()
    stats = await study.get_user_stats(user_id)
    roleInfo = await study.get_user_role_info(user_id)
    username = await study.get_username_from_user_id(user_id)
    # study.close()
    return {"username": username, "stats": stats, "roleInfo": roleInfo}


@app.route("/usertimeseries/<user_id>")
async def get_user_timeseries(user_id):
    # abort_if_user_doesnt_exist(user_id)
    # study = Study()
    study = await get_study()
    time_interval = request.args.get("time_interval")
    if not time_interval:
        abort(404)
    timeseries = await study.get_user_timeseries(user_id, time_interval)
    neighbors = await study.get_neighbor_stats(time_interval, user_id)
    # study.close()
    return jsonify({"timeseries": timeseries, "neighbors": neighbors})


@app.route("/leaderboard")
async def get_leaderboard():
    # args = args_parser.parse_args()
    # study = Study()
    study = await get_study()
    print("Study:")
    print(study)
    offset = request.args.get("offset")
    limit = request.args.get("limit")

    try:
        offset = int(offset)
        limit = int(limit)
    except:
        abort(404)

    time_interval = request.args.get("time_interval")
    # study.close()
    return await study.get_leaderboard(offset, limit, time_interval)


@app.route("/users")
async def username_lookup():
    match = request.args.get("match")
    matching_users = await ipc_client.request(
        "search_users", guild_id=os.getenv("guildID"), match=match
    )  # get the member count of server with ID 12345678

    return jsonify(matching_users)  # display member count


# @app.route("/users")
# async def username_lookup():
#     # args = args_parser.parse_args()
#     # study = Study()
#     # matching_users = study.get_matching_users(match)
#     # print(matching_users)
#     # study.close()
#     return jsonify(matching_users)

# async def initialize_study():
#     study = await Study.create()
#     await study.get_leaderboard(0, 5, 'pastWeek')


if __name__ == "__main__":

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(initialize_study())
    # app.run(loop=loop, debug=True)
    app.run(debug=True)
