import os
from typing import Any

from dotenv import load_dotenv
from models import User
from sqlalchemy.future import select

from common import async_utilities as utilities

load_dotenv("dev.env")


class Study:
    def __init__(self, redis_client, engine, ipc_client, ipc_lock):
        self.role_name_to_obj = utilities.config[
            ("test_" if os.getenv("mode") == "test" else "") + "study_roles"
        ]
        self.redis_client = redis_client
        self.engine = engine
        # 
        self.ipc_client = ipc_client
        # lock for ensuring ipc_client is only requesting once at a time
        self.ipc_lock = ipc_lock

    async def user_exists(self, discord_user_id):
        """
        Check if a user exists in the server with a discord user id
        """
        stmt = select(User).filter(User.id == int(discord_user_id))

        async with self.engine.connect() as connection:
            user_sql_obj = (await connection.execute(stmt)).first()

        # if user exists return true, otherwise false
        if user_sql_obj:
            return True
        else:
            return False


    async def username_lookup(self, match):
        async with self.ipc_lock:
            return await self.ipc_client.request(
                "search_users", match=match
            )


    async def get_username_from_user_id(self, id):
        """
        Get a users name from their discord user id

        Uses ipc to communicate with a discord bot
        """
        async with self.ipc_lock:
            return await self.ipc_client.request(
                "user_id_to_username", user_id=id
               )

    async def get_user_stats(self, id):
        """
        Return a user's stats from their id
        """
        timepoint = f"daily_{utilities.get_day_start()}"
        stmt = select(User).filter(User.id == int(id))
        # engine = await utilities.get_sql_engine()
        async with self.engine.connect() as connection:
            user_sql_obj = (await connection.execute(stmt)).first()

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
        adjust = max(0, 5 - rank)

        id_with_score = await self.get_info_from_leaderboard(
            sorted_set_name, rank - 5 + adjust, rank + 5 + adjust
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
            async with self.ipc_lock:
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
            async with self.ipc_lock:
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

        async with self.ipc_lock:
            num_users = await self.ipc_client.request("get_member_count")


        return {"leaderboard": id_with_score, "num_users": num_users}
