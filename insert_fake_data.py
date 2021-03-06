import os
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Mapping

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

from common import utilities
from models import Action, Base, User, action_categories

load_dotenv("dev.env")

database_name = os.getenv("database")

seed = os.getenv("seed")
seed = int(seed) if seed else 0

random.seed(seed)
np.random.seed(seed)

engine = utilities.get_engine()
Session = sessionmaker(bind=engine)
sqlalchemy_session = Session()
redis_client = utilities.get_redis_client()

user_size = 50000
# action_size = user_size * 30 * 3 + 1


def generate_user_df():
    user_df = pd.DataFrame()
    user_df["id"] = utilities.generate_random_number(user_size)
    user_df["username"] = utilities.generate_random_usernames(user_size)
    user_df["tag"] = utilities.generate_random_tags(user_size)
    current_streak = [random.randint(0, 10) for _ in range(user_size)]
    user_df["current_streak"] = current_streak
    user_df["longest_streak"] = [i + random.randint(0, 5) for i in current_streak]

    # "append" means not creating a new table
    user_df.to_sql("user", con=engine, if_exists="append", index=False)
    sqlalchemy_session.commit()


def generate_sorted_set():
    filter_time_fn_li = [
        utilities.get_day_start,
        utilities.get_week_start,
        utilities.get_month_start,
        utilities.get_earliest_start,
    ]
    category_key_names = utilities.get_rank_categories().values()

    query = sqlalchemy_session.query(User.id)
    # user_ids: List[str] = list(map(lambda x: str(x), list(query.all())))
    # print(user_ids)
    response = pd.read_sql(query.statement, sqlalchemy_session.bind)

    # # print(response)
    user_id_list = response["id"].to_list()
    # print(user_id_list)

    # day
    day_timepoint = utilities.get_day_start()
    daily_timepoints = [
        "daily_" + str(day_timepoint - i * timedelta(days=1)) for i in range(60)
    ]

    for sorted_set_name in daily_timepoints:

        to_insert = dict()
        for user_id in user_id_list:
            to_insert[user_id] = random.randint(0, 16 * 10) / 10
        redis_client.zadd(sorted_set_name, to_insert)

    # week
    week_timepoint = utilities.get_week_start()
    weekly_timepoints = [
        "weekly_" + str(week_timepoint - i * timedelta(days=7)) for i in range(6)
    ]

    for sorted_set_name in weekly_timepoints:

        to_insert = dict()
        for user_id in user_id_list:
            to_insert[user_id] = random.randint(0, 16 * 7 * 10) / 10
        redis_client.zadd(sorted_set_name, to_insert)

    # month
    month_timepoint = utilities.get_month()
    to_insert = dict()
    for user_id in user_id_list:
        to_insert[user_id] = random.randint(0, 16 * 7 * 4 * 10) / 10
    redis_client.zadd("monthly_" + str(month_timepoint), to_insert)
    redis_client.zadd("all_time", to_insert)


# def generate_username_mapping():
# 
#     query = sqlalchemy_session.query(User.id)
#     response = pd.read_sql(query.statement, sqlalchemy_session.bind)
# 
#     # get list of user ids
#     user_id_list = response["id"].to_list()
# 
#     # generate mapping from user ids to usernames
#     user_id_to_username = dict()
#     user_id_to_username.update(
#         {
#             user_id: "".join(random.choice(string.ascii_lowercase) for i in range(10))
#             for user_id in user_id_list
#         }
#     )
# 
#     # generate mapping from usernames to user ids
#     username_to_user_id = dict()
#     username_to_user_id = {v: k for k, v in user_id_to_username.items()}
# 
#     # save the mappings to redis
#     redis_client.hmset("user_id_to_username", user_id_to_username)
#     redis_client.hmset("username_to_user_id", username_to_user_id)


if __name__ == "__main__":
    utilities.recreate_db(Base)
    generate_user_df()
    generate_sorted_set()
    # generate_username_mapping()
