from flask import Flask, abort, g, jsonify, request

from common.study import Study

app = Flask(__name__)

# args_parser.add_argument("offset", type=int)
# args_parser.add_argument("limit", type=int)
# args_parser.add_argument("time_interval", type=str)
# args_parser.add_argument("match", type=str)

# study = Study()

# def abort_if_user_doesnt_exist(discord_user_id):
#     if not study.user_exists(discord_user_id):
#         abort(404, message="User {} doesn't exist".format(discord_user_id))


# def connect_study():
#     return Study()
# 
# def get_study():
#     if not hasattr(g, 'study'):
#         g.study = connect_study()
#     return g.study
# 
# @app.teardown_appcontext
# def close_study(e):
#     if hasattr(g, 'study'):
#         g.study.close()


@app.route("/userstats/<user_id>")
def get_user_stats(user_id):
    # abort_if_user_doesnt_exist(user_id)
    study = Study()
    stats = study.get_user_stats(user_id)
    roleInfo = study.get_user_role_info(user_id)
    username = study.get_username_from_user_id(user_id)
    study.close()
    return {"username": username, "stats": stats, "roleInfo": roleInfo}

@app.route("/usertimeseries/<user_id>")
def get_user_timeseries(user_id):
    # abort_if_user_doesnt_exist(user_id)
    study = Study()
    time_interval = request.args.get("time_interval")
    if not time_interval:
        abort(404)
    timeseries = study.get_user_timeseries(user_id, time_interval)
    neighbors = study.get_neighbor_stats(time_interval, user_id)
    study.close()
    return jsonify({"timeseries": timeseries, "neighbors": neighbors})

@app.route("/leaderboard")
def get_leaderboard():
    # args = args_parser.parse_args()
    study = Study()
    offset = (request.args.get("offset"))
    limit = request.args.get("limit")

    try:
        offset = int(offset)
        limit = int(limit)
    except:
        abort(404)

    time_interval = request.args.get("time_interval")
    study.close()
    return study.get_leaderboard(offset, limit, time_interval)

@app.route("/users")
def username_lookup():
    # args = args_parser.parse_args()
    study = Study()
    match = request.args.get("match")
    matching_users = study.get_matching_users(match)
    # print(matching_users)
    study.close()
    return jsonify(matching_users)

if __name__ == "__main__":
    app.run(debug=True, threaded=False)

