import os
import random
from datetime import timedelta
from typing import Any

from discord.ext import ipc
from dotenv import load_dotenv
from models import Action, User
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from common import async_utilities as utilities

load_dotenv("dev.env")


class Study:
    def __init__(self, ipc_client, lock):
        # self.engine = utilities.get_engine()
        # self.sqlalchemy_session = sessionmaker(bind=self.engine)()
        # self.sqlalchemy_session = await utilities.get_sql_session()
        # self.redis_client = utilities.get_redis_client()
        self.lock = lock
        self.ipc_client = ipc_client
        self.session: Any = None
        self.redis_client: Any = None
        self.role_name_to_obj = utilities.config[
            ("test_" if os.getenv("mode") == "test" else "") + "study_roles"
        ]

    @classmethod
    async def create(cls, ipc_client, lock):
        self = Study(ipc_client, lock)
        self.session = await utilities.get_sql_session()
        self.redis_client = await utilities.get_redis_client()
        # self.ipc_client = ipc.Client(secret_key="my_secret_key")
        return self

        # verify that connection to server succeeded
        # self.redis_client.ping()

    # def close(self):
    #     utilities.commit_or_rollback(self.sqlalchemy_session)
    #     self.sqlalchemy_session.close()
    #     self.engine.dispose()

    # def save(self):
    #     utilities.commit_or_rollback(self.sqlalchemy_session)

    # async def user_exists(self, discord_user_id):
    #     try:
    #         stmt = select(User).filter(User.id == int(discord_user_id))
    #         result = await stmt
    #         return result.first()
    #         # user_sql_obj = (
    #         #     self.sqlalchemy_session.query(User)
    #         #     .filter(User.id == int(discord_user_id))
    #         #     .first()
    #         # )
    #     except:
    #         return False

    #     if user_sql_obj:
    #         return True
    #     else:
    #         return False

    # def get_username_from_user_id(self, discord_user_id):
    #     user = self.sqlalchemy_session.query(User).filter(User.id == int(discord_user_id)).first()
    #     return user.username


    # def get_matching_users(self, match):
    #     res = []
    #     users = self.sqlalchemy_session.query(User).filter(User.username.like(f"%{match}%")).limit(15).all()
    #     for user in users:
    #         res.append(
    #             {
    #                 "username": user.username,
    #                 "discord_user_id": str(user.id),
    #                 "tag": f"#{user.tag}",
    #             }
    #         )

        # for username, user_id in self.redis_client.hscan(
        #     "username_to_user_id", 0, match=f"*{match}*"
        # )[1].items():
        #     res.append(
        #         {
        #             "username": username,
        #             "discord_user_id": user_id,
        #             "tag": f"#{random.randint(0, 9999):02d}",
        #         }
        #     )


        # return res

    async def get_username_from_user_id(self, id):
        async with self.lock:
            return await self.ipc_client.request(
                "user_id_to_username", user_id=id
               )


    async def get_user_stats(self, id):
        """
        return a users stats from their id
        """
        timepoint = f"daily_{utilities.get_day_start()}"
        stmt = select(User).filter(User.id == int(id))
        # session = await utilities.get_sql_session()
        user_sql_obj = (await self.session.execute(stmt)).scalars().first()
        # print(user_sql_obj)
        # print(repr(user_sql_obj[0]))
        # print(user_sql_obj[0].id)
        # print(user_sql_obj[0]._mapping.items())

        # print(user_sql_obj.items()id)
        # try:
        #     user_sql_obj = (
        #         self.sqlalchemy_session.query(User).filter(User.id == int(id)).first()
        #     )
        # except:
        #     utilities.commit_or_rollback(self.sqlalchemy_session)

        stats = await utilities.get_time_interval_user_stats(
            self.redis_client, id, timepoint=timepoint
        )
        stats["average_per_day"] = utilities.round_num(
            stats["pastMonth"]["study_time"] / utilities.get_num_days_this_month()
        )

        stats["currentStreak"] = user_sql_obj.current_streak if user_sql_obj else 0
        stats["longestStreak"] = user_sql_obj.longest_streak if user_sql_obj else 0

        return stats

    async def get_user_role_info(self, id):
        user_id = id
        rank_categories = utilities.get_rank_categories()

        hours_cur_month = await utilities.get_redis_score(
            self.redis_client, rank_categories["monthly"], user_id
        )
        if not hours_cur_month:
            hours_cur_month = 0

        role, next_role, time_to_next_role = utilities.get_role_status(
            self.role_name_to_obj, hours_cur_month
        )

        if not next_role:
            next_role = role
            time_to_next_role = 0

        return {
            "role": role,
            "next_role": next_role,
            "time_to_next_role": time_to_next_role,
        }

    async def get_neighbor_stats(self, time_interval, user_id):

        timepoint = utilities.time_interval_to_timepoint(time_interval)
        sorted_set_name = timepoint

        rank = await utilities.get_redis_rank(self.redis_client, sorted_set_name, user_id)
        rank -= 1  # Use 0 index
        id_with_score = await self.get_info_from_leaderboard(
            sorted_set_name, rank - 5, rank + 5
        )

        return id_with_score

    async def get_info_from_leaderboard(self, sorted_set_name, start=0, end=-1):
        if start < 0:
            start = 0

        id_li = [
            int(i) for i in await self.redis_client.zrevrange(sorted_set_name, start, end)
        ]
        id_with_score = []

        for neighbor_id in id_li:
            res = dict()
            res["discord_user_id"] = str(neighbor_id)
            async with self.lock:
                res["username"] = await self.ipc_client.request(
                    "user_id_to_username", user_id=neighbor_id
                   )
            res["rank"] = await utilities.get_redis_rank(
                self.redis_client, sorted_set_name, neighbor_id
            )
            res["study_time"] = await utilities.get_redis_score(
                self.redis_client, sorted_set_name, neighbor_id
            )
            id_with_score.append(res)

        return id_with_score

    async def get_user_timeseries(self, id, time_interval):
        timeseries = await utilities.get_user_timeseries(self.redis_client, id, time_interval)
        return timeseries


    async def get_leaderboard(self, offset, limit, time_interval):
        timepoint = utilities.time_interval_to_timepoint(time_interval)
        start = offset
        end = offset + limit

        sorted_set_name = timepoint

        if start < 0:
            start = 0

        id_list = [
            int(i) for i in await self.redis_client.zrevrange(sorted_set_name, start, end)
        ]
        id_with_score = []


        # ipc_client = ipc.Client(secret_key="my_secret_key")


        for neighbor_id in id_list:
            res = dict()
            res["discord_user_id"] = str(neighbor_id)
            # res["username"] = "Cole"
            async with self.lock:
                res["username"] = await self.ipc_client.request(
                    "user_id_to_username", user_id=neighbor_id
                   )
            res["rank"] = await utilities.get_redis_rank(
                self.redis_client, sorted_set_name, neighbor_id
            )
            res["study_time"] = await utilities.get_redis_score(
                self.redis_client, sorted_set_name, neighbor_id
            )
            id_with_score.append(res)

        async with self.lock:
            num_users = await self.ipc_client.request("get_member_count")


        return {"leaderboard": id_with_score, "num_users": num_users}
