from flask import Flask
from flask_restful import Api, Resource, abort, reqparse

from common.study import Study

app = Flask(__name__)
api = Api(app)

args_parser = reqparse.RequestParser()
args_parser.add_argument("offset", type=int)
args_parser.add_argument("limit", type=int)
args_parser.add_argument("time_interval", type=str)
args_parser.add_argument("match", type=str)

study = Study()


class Leaderboard(Resource):
    def get(self):
        args = args_parser.parse_args()
        return study.get_leaderboard(args.offset, args.limit, args.time_interval)


class UserStats(Resource):
    def get(self, user_id):
        stats = study.get_user_stats(user_id)
        roleInfo = study.get_user_role_info(user_id)
        username = study.get_username_from_user_id(user_id)
        return {"username": username, "stats": stats, "roleInfo": roleInfo}


class UserTimeSeries(Resource):
    def get(self, user_id):
        args = args_parser.parse_args()
        timeseries = study.get_user_timeseries(user_id, args.time_interval)
        neighbors = study.get_neighbor_stats(args.time_interval, user_id)

        return {"timeseries": timeseries, "neighbors": neighbors}


class UsernameLookup(Resource):
    def get(self):
        args = args_parser.parse_args()
        matching_users = study.get_matching_users(args.match)
        print(matching_users)
        return matching_users


api.add_resource(UserStats, "/userstats/<user_id>")
api.add_resource(UserTimeSeries, "/usertimeseries/<user_id>")
api.add_resource(Leaderboard, "/leaderboard")
api.add_resource(UsernameLookup, "/users")

if __name__ == "__main__":
    app.run(debug=True)
