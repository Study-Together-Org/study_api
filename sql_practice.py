import asyncio
import os
import random
import string
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import aioredis
import dateparser
import hjson
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.future import select

from models import DailyStudyTime

load_dotenv("dev.env")

Faker.seed(int(os.getenv("seed")))
fake = Faker()

# num_uuid = shortuuid.ShortUUID()
# num_uuid.set_alphabet("0123456789")  # uuid that only has numbers
back_range = 61

with open("config.hjson") as f:
    config = hjson.load(f)

key_name = ("test_" if os.getenv("mode") == "test" else "") + "study_roles"
role_settings = config[key_name]
role_name_to_begin_hours = {
    role_name: float(role_info["hours"].split("-")[0])
    for role_name, role_info in role_settings.items()
}
role_names = list(role_settings.keys())

num_intervals = 24 * 1
delta = timedelta(days=1)
interval = delta / num_intervals


def get_rank_categories(flatten=False, string=True):
    """
    In general, it's easier to convert datetime objects to strings than the other way around; this function can give both
    """
    rank_categories = {}

    if flatten:
        timepoints = get_earliest_timepoint(prefix=True, string=string)
    else:
        timepoints = get_timepoints()
        if string:
            timepoints = ["daily_" + str(timepoint) for timepoint in timepoints]

    rank_categories["daily"] = timepoints
    rank_categories["weekly"] = f"weekly_{get_week_start()}"
    rank_categories["monthly"] = f"monthly_{get_month()}"
    rank_categories["all_time"] = "all_time"

    return rank_categories


def get_guildID():
    guildID_key_name = ("test_" if os.getenv("mode") == "test" else "") + "guildID"
    guildID = int(os.getenv(guildID_key_name))
    return guildID


def recreate_db(Base):
    redis_client = get_redis_client()
    engine = get_engine()
    # redis_client.flushall()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def get_engine(echo=False):
    return create_engine(
        f'mysql+pymysql://{os.getenv("sql_user")}:{os.getenv("sql_password")}@{os.getenv("sql_host")}/{os.getenv("sql_database")}',
        echo=echo,
    )


async def get_engine_pool(echo=False):
    async_engine = create_async_engine(
        f'mysql+aiomysql://{os.getenv("sql_user")}:{os.getenv("sql_password")}@{os.getenv("sql_host")}/{os.getenv("sql_database")}',
        echo=echo,
        pool_size=20
    )
    # async_session = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
    return async_engine


def get_time():
    now = datetime.utcnow()
    return now


def get_num_days_this_month():
    return datetime.utcnow().day


def get_day_start():
    date = datetime.combine(datetime.utcnow().date(), datetime.min.time())
    offset = timedelta(hours=config["business"]["update_time"])

    if datetime.utcnow() < date + offset:
        offset -= timedelta(days=1)

    return date + offset


def get_tomorrow_start():
    return get_day_start() + timedelta(days=1)


def get_week_start():
    return get_day_start() - timedelta(days=get_day_start().weekday() % 7)


def get_month_start():
    given_date = get_day_start()
    first_day_of_month = given_date - timedelta(days=int(given_date.strftime("%d")) - 1)
    return first_day_of_month


def get_earliest_start():
    return datetime.utcnow() - timedelta(days=back_range)


def get_month():
    return datetime.utcnow().strftime("%B")


def get_earliest_timepoint(starting_point=None, string=False, prefix=False):
    if not starting_point:
        starting_point = get_time() - delta

    offset = interval - (starting_point - datetime(1900, 1, 1)) % interval

    if offset == interval:
        offset -= interval

    earliest_timepoint = starting_point + offset
    return (
        f"{'daily_' if prefix else ''}{earliest_timepoint}"
        if string
        else earliest_timepoint
    )


def parse_time(timepoint, zone_obj=ZoneInfo(config["business"]["timezone"])):
    if timepoint is None:
        timepoint = ""

    if len(timepoint) > 30:
        return

    # This library is very flexible; some functions even support non-English languages
    parsed = dateparser.parse(
        timepoint, date_formats=["%H:%M", "%H:%m", "%h:%M", "%h:%m", "%H", "%h"]
    )

    if not parsed:
        return

    if parsed.replace(tzinfo=zone_obj) >= datetime.now(zone_obj):
        parsed -= timedelta(days=1)

    return parsed


def get_closest_timepoint(full_time_point, prefix=False):
    cur_time = get_time()

    if full_time_point > cur_time:
        full_time_point -= timedelta(days=1)

    timepoint_to_use = get_earliest_timepoint(full_time_point, string=True)

    return f"{'daily_' if prefix else ''}{timepoint_to_use}"


def get_timepoints():
    earliest_timepoint = get_earliest_timepoint(prefix=False)
    timepoints = [earliest_timepoint + i * interval for i in range(num_intervals)]
    return timepoints


def timedelta_to_hours(td):
    return td.total_seconds() / 3600


def round_num(num, ndigits=None):
    if not ndigits:
        ndigits_var_name = (
                               "test_" if os.getenv("mode") == "test" else ""
                           ) + "display_num_decimal"
        ndigits = int(os.getenv(ndigits_var_name))

    return round(num, ndigits=ndigits)


def calc_total_time(data):
    if not data:
        return 0

    total_time = timedelta(0)
    start_idx = 0
    end_idx = len(data) - 1

    if data[0]["category"] == "end channel":
        total_time += data[0]["creation_time"] - get_month_start()
        start_idx = 1

    if data[-1]["category"] == "start channel":
        total_time += get_time() - data[-1]["creation_time"]
        end_idx -= 1

    for idx in range(start_idx, end_idx + 1, 2):
        total_time += data[idx + 1]["creation_time"] - data[idx]["creation_time"]

    total_time = timedelta_to_hours(total_time)
    return total_time


def generate_random_number(size=1, length=18):
    res = [fake.random_number(digits=length, fix_len=True) for _ in range(size)]
    return res


def generate_random_usernames(size=1, length=10):
    return ["".join(random.choice(string.ascii_lowercase) for _ in range(length)) for _ in range(size)]


def generate_random_tags(size=1):
    return [f"{random.randint(0, 9999):04d}" for _ in range(size)]


def generate_discord_user_id(size=1, length=18):
    res = []

    if size >= 2:
        res += [
            int(os.getenv("tester_human_discord_user_id")),
            int(os.getenv("tester_bot_token_discord_user_id")),
        ]
        size -= 2

    res += generate_random_number(size, length)

    return res


def generate_datetime(size=1, start_date=f"-{back_range}d"):
    return sorted(
        [
            fake.past_datetime(start_date=start_date, tzinfo=timezone.utc)
            for _ in range(size)
        ]
    )


def generate_username(size=1):
    return [fake.user_name() for _ in range(size)]


async def get_redis_pool():
    port = os.getenv("redis_port")
    username = os.getenv("redis_username")
    password = os.getenv("redis_password")
    host = os.getenv("redis_host")
    db = os.getenv("redis_db_num")
    if username is not None and password is not None:
        return await aioredis.create_redis_pool(f"redis://{username}:{password}@{host}:{port}/{db}", minsize=10,
                                                maxsize=20)
    else:
        return await aioredis.create_redis_pool(f"redis://@{host}:{port}/{db}", minsize=10, maxsize=20)


async def get_redis_client():
    port = os.getenv("redis_port")
    username = os.getenv("redis_username")
    password = os.getenv("redis_password")
    host = os.getenv("redis_host")
    db = os.getenv("redis_db_num")
    return await aioredis.create_redis_pool(f"redis://{username}:{password}@{host}:{port}/{db}")
    # return redis.Redis(
    #     host=os.getenv("redis_host"),
    #     port=os.getenv("redis_port"),
    #     db=int(os.getenv("redis_db_num")),
    #     username=os.getenv("redis_username"),
    #     password=os.getenv("redis_password"),
    #     decode_responses=True,
    # )


def get_role_status(role_name_to_obj, hours_cur_month):
    cur_role_name = role_names[0]
    next_role_name = role_names[1]

    for role_name, begin_hours in role_name_to_begin_hours.items():
        if begin_hours <= hours_cur_month:
            cur_role_name = role_name
        else:
            next_role_name = role_name
            break

    cur_role = role_name_to_obj[cur_role_name]
    # new members
    if hours_cur_month < role_name_to_begin_hours[cur_role_name]:
        cur_role = None

    next_role, time_to_next_role = (
        (
            role_name_to_obj[next_role_name],
            round_num(role_name_to_begin_hours[next_role_name] - hours_cur_month),
        )
        if cur_role_name != role_names[-1]
        else (None, None)
    )

    return cur_role, next_role, time_to_next_role


def get_last_line():
    try:
        with open("heartbeat.log", "rb") as f:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b"\n":
                f.seek(-2, os.SEEK_CUR)
            line = f.readline().decode()
        return line
    except OSError:
        return None


def get_last_time(line):
    last_line = " ".join(line.split()[:2])
    return datetime.strptime(last_line, str(os.getenv("datetime_format")))


async def get_redis_rank(redis_client, sorted_set_name, user_id):
    rank = await redis_client.zrevrank(sorted_set_name, user_id)

    # print(user_id)
    if rank is None:
        await redis_client.zadd(sorted_set_name, 0, user_id)
        rank = await redis_client.zrevrank(sorted_set_name, user_id)

    return 1 + rank


async def get_redis_score(redis_client, sorted_set_name, user_id):
    score = await redis_client.zscore(sorted_set_name, user_id) or 0
    return round_num(score)


async def get_time_interval_user_stats(
        redis_client, user_id, timepoint=get_earliest_timepoint(string=True, prefix=True)
):
    stats = dict()
    category_key_names = list(get_rank_categories().values())

    for sorted_set_name in [timepoint] + category_key_names[1:]:
        stats[get_time_interval_from_timepoint(sorted_set_name)] = {
            "rank": await get_redis_rank(redis_client, sorted_set_name, user_id),
            "study_time": await get_redis_score(redis_client, sorted_set_name, user_id),
        }

    return stats


def get_time_interval_from_timepoint(timepoint):
    if "daily" in timepoint:
        return "pastDay"
    elif "weekly" in timepoint:
        return "pastWeek"
    elif "monthly" in timepoint:
        return "pastMonth"
    elif "all_time" in timepoint:
        return "allTime"
    else:
        print("ERROR get_time_interval_from_timepoint")
        return "error"


async def get_timeseries_timepoint(redis_client, engine, sorted_set_name, user_id):
    tasks = [
        get_redis_rank(redis_client, sorted_set_name, user_id),
        get_redis_score(redis_client, sorted_set_name, user_id),
    ]
    done = await asyncio.gather(*tasks)

    return {"date": sorted_set_name[6:-9], "rank": done[0], "study_time": done[1]}  # type: ignore


async def get_user_timeseries(redis_client, engine, user_id, time_interval):
    # convert from time interval to number of days
    time_interval_to_span = {
        "pastDay": 1,
        "pastWeek": 7,
        "pastMonth": (get_day_start() - get_month_start()).days + 1,
        "allTime": 500,
    }
    span = time_interval_to_span[time_interval]

    # get the interested timepoints
    timepoint = get_day_start()
    timepoints = [
        "daily_" + str(timepoint - i * timedelta(days=1)) for i in range(span)
    ]

    # query sql dailystudytime table for information
    async with engine.connect() as connection:
        stmt = select(DailyStudyTime).filter(DailyStudyTime.user_id == user_id).filter(
            DailyStudyTime.timestamp >= get_day_start() - timedelta(days=span))

        # this is a list of tuples of datetime objects
        sql_rows = (await connection.execute(stmt)).all()

        sql_dicts = [{
            "date": row.timestamp.strftime("%y-%m-%d"),
            "rank": row.rank,
            "study_time": row.study_time
        } for row in sql_rows if row.timestamp.hour == 17]

        sql_str_datetimes = set(row.timestamp.strftime(f"daily_{os.getenv('datetime_format').split('.')[0]}") for row in
                                sql_rows)

    tasks = []
    for sorted_set_name in timepoints:
        # if not found in sql
        if sorted_set_name not in sql_str_datetimes:
            tasks.append(get_timeseries_timepoint(redis_client, engine, sorted_set_name, user_id))

    redis_dicts = list(await asyncio.gather(*tasks))

    timeseries = list(reversed(redis_dicts + sql_dicts))

    if time_interval == "allTime":
        c = 0
        while c < len(timeseries) and timeseries[c]["study_time"] == 0:
            c += 1
        timeseries = timeseries[c:]

    return timeseries


def time_interval_to_timepoint(time_interval):
    return {
        "pastDay": f"daily_{get_day_start()}",
        "pastWeek": f"weekly_{get_week_start()}",
        "pastMonth": f"monthly_{get_month()}",
        "allTime": "all_time",
    }[time_interval]


async def main():
    redis = None
    engine = await get_engine_pool()
    timeseries = await get_user_timeseries(redis, engine, 683274515798949889, "pastMonth")
    print(timeseries)
    await engine.dispose()


asyncio.run(main())
