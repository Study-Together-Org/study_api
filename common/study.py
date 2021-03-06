import os

from dotenv import load_dotenv
import asyncio
from models import User
from sqlalchemy.future import select

from common import async_utilities as utilities

load_dotenv("dev.env")


class Study:
    def __init__(self, redis_client, engine, discord_bot):
        self.role_name_to_obj = utilities.config[
            ("test_" if os.getenv("mode") == "test" else "") + "study_roles"
            ]
        self.redis_client = redis_client
        self.engine = engine
        self.discord_bot = discord_bot

    async def user_exists(self, discord_user_id):
        """
        Check if a user exists in the server with a discord user id

        Parameters:
        - discord_user_id (str): user id to check if exists
        """
        try:
            discord_user_id = int(discord_user_id)
        except:
            # not an int
            return False

        stmt = select(User).filter(User.id == int(discord_user_id))

        async with self.engine.connect() as connection:
            user_sql_obj = (await connection.execute(stmt)).first()

        # if user exists return true, otherwise false
        if user_sql_obj:
            return True
        else:
            return False

    async def username_lookup(self, match):
        """
        Return a list of users matching a prefix
        """
        return await self.discord_bot.search_users(match)

    async def get_username_from_user_id(self, user_id):
        """
        Get a users name from their discord user id
        """
        return await self.discord_bot.user_id_to_username(user_id)

    async def get_user_stats(self, user_id):
        """
        Return a user's stats from their id
        """
        timepoint = f"daily_{utilities.get_day_start()}"
        stmt = select(User).filter(User.id == int(user_id))
        async with self.engine.connect() as connection:
            user_sql_obj = (await connection.execute(stmt)).first()

        stats = await utilities.get_time_interval_user_stats(
            self.redis_client, user_id, timepoint=timepoint
        )

        stats["averagePerDay"] = utilities.round_num(
            stats["pastMonth"]["study_time"] / utilities.get_num_days_this_month()
        )

        stats["currentStreak"] = user_sql_obj.current_streak if user_sql_obj else 0
        stats["longestStreak"] = user_sql_obj.longest_streak if user_sql_obj else 0

        return stats

    async def get_user_role_info(self, user_id):
        """
        Get a users role info from their id
        """
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

    async def get_user_timeseries(self, id, time_interval):
        """
        Get a user's timeseries data
        """
        timeseries = await utilities.get_user_timeseries(self.redis_client, self.engine, id, time_interval)
        return timeseries

    async def get_neighbor_stats(self, time_interval, user_id):
        """
        Get the neighbors of a user by id for a certain time_interval
        """

        timepoint = utilities.time_interval_to_timepoint(time_interval)
        sorted_set_name = timepoint

        rank = await utilities.get_redis_rank(self.redis_client, sorted_set_name, user_id)
        rank -= 1  # Use 0 index
        adjust = max(0, 5 - rank)

        id_with_score = await self.get_info_from_leaderboard(
            sorted_set_name, rank - 5 + adjust, rank + 5 + adjust
        )

        return id_with_score

    async def get_user_rank_and_score(self, sorted_set_name, user_id):
        """
        Return a leaderboard row dict for a user_id
        """
        res = dict()
        res["rank"] = await utilities.get_redis_rank(
            self.redis_client, sorted_set_name, user_id
        )
        res["study_time"] = await utilities.get_redis_score(
            self.redis_client, sorted_set_name, user_id
        )
        return res

    async def get_info_from_leaderboard(self, sorted_set_name, start=0, end=-1):
        """
        Get leaderboard information with start and end flags

        Used for getting the neighbors of a user
        """
        if start < 0:
            start = 0

        id_li = [
            int(i) for i in await self.redis_client.zrevrange(sorted_set_name, start, end)
        ]

        usernames = await self.discord_bot.user_ids_to_usernames(id_li)

        tasks = []
        for neighbor_id in id_li:
            tasks.append(self.get_user_rank_and_score(sorted_set_name, neighbor_id))

        user_ranks_and_study_times = await asyncio.gather(*tasks)

        return [
            {"discord_user_id": str(user_id), "username": username, "rank": stats["rank"],
             "study_time": stats["study_time"]}
            for user_id, username, stats in zip(id_li, usernames, user_ranks_and_study_times)]

    async def get_leaderboard(self, offset, limit, time_interval):
        """
        Get leaderboard information and num_users

        Used for populating the leaderboard table
        """
        sorted_set_name = utilities.time_interval_to_timepoint(time_interval)
        start = offset
        end = offset + limit

        leaderboard = await self.get_info_from_leaderboard(sorted_set_name, start, end)

        num_users = await self.discord_bot.get_member_count()

        return {"leaderboard": leaderboard, "num_users": num_users}