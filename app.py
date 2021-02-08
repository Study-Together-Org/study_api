from flask import Flask
from flask_restful import Api, Resource, abort, reqparse

from common.study import Study

app = Flask(__name__)
api = Api(app)

args_parser = reqparse.RequestParser()
args_parser.add_argument('offset', type=int)
args_parser.add_argument('limit', type=int)
args_parser.add_argument('time_interval', type=str)

study = Study()

class Leaderboard(Resource):
    def get(self):
        args = args_parser.parse_args()
        return study.getLeaderboard(args.offset, args.limit, args.time_interval)

class UserStats(Resource):
    def get(self, user_id):
        stats = study.getUserStats(user_id)
        roleInfo = study.getUserRoleInfo(user_id)
        return {
            'stats': stats,
            'roleInfo': roleInfo
        }

class UserTimeSeries(Resource):
    def get(self, user_id):
        args = args_parser.parse_args()
        timeseries = study.getUserTimeSeries(user_id, args.time_interval)
        neighbors = study.get_neighbor_stats(args.time_interval, user_id)

        return {
            'timeseries': timeseries,
            'neighbors': neighbors
        }

api.add_resource(UserStats, '/userstats/<user_id>')
api.add_resource(UserTimeSeries, '/usertimeseries/<user_id>')
api.add_resource(Leaderboard, '/leaderboard')

if __name__ == '__main__':
    app.run(debug=True)
