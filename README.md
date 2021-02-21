# Study Together Flask Api

This is a restful flask api for querying data related to study together.

# Getting Started

## Basic Development Environment

Setup redis and mysql with fake data.

1. Mariadb

[Install](https://wiki.archlinux.org/index.php/MariaDB) and start mariadb.


Create a studytogether database:
```mysql
# create studytogether database
CREATE DATABASE studytogether
```

Create a user with access to the studytogether database:
```
$ mysql -u root -p
MariaDB> CREATE USER 'study'@'localhost' IDENTIFIED BY 'study_pass';
MariaDB> GRANT ALL PRIVILEGES ON studytogether.* TO 'study'@'localhost';
MariaDB> FLUSH PRIVILEGES;
MariaDB> quit
```

2. Redis

[Install](https://wiki.archlinux.org/index.php/redis) and start redis.

3. Populate dev.env

```bash
# Copy example to dev.env and populate it 
cp dev.env.example dev.env
```

4. Insert fake data

This will run migrations and then insert fake data into the mysql and redis dbs.
```bash
pipenv install
pipenv shell
python insert_fake_data.py
```

5. Start the Api

This will start the flask api on port 5000.
```bash
pipenv shell
python app.py
```

## Get the id of a user

In order to use queries you need to use the id of a valid user. You can get a valid id as follows:

```bash
$ mysql -u study -p
MariaDB> USE studytogether;
MariaDB> SELECT * FROM user LIMIT 10;
```

# Usage

There are four main queries:

## users

Return a list of matching users and their userids.

Takes a param for match. The list of users will be searched by the glob `f"*{match}*"`.

Example call:

```
http://localhost:5000/users?match=hi
```

Example response:

```
{
    "phixltkpvm": "215270539886472525",
    "hizxfwuhhw": "593950567587474809",
    "znyxihipjl": "675574458552210453",
    "pbyvmwwphi": "714168395175613125",
    "sghlchiemd": "948247212994799808"
}
```


## leaderboard

Returns leaderboard information on a time interval. 

Takes params for offset, limit, and time_interval. Time interval must be one of "pastDay", "pastWeek", "pastMonth", "allTime".

Example call: 
```
leaderboard?offset=0&limit=5&time_interval=pastWeek
```

Example response:

```
[
    {
        "discord_user_id": 754118016803749048,
        "username": "yvniooxeuk",
        "rank": 1,
        "study_time": 70.0
    },
    {
        "discord_user_id": 927698802236956910,
        "username": "esqqbzrlrh",
        "rank": 2,
        "study_time": 68.0
    },
    {
        "discord_user_id": 290378422076173744,
        "username": "olbtvlinkv",
        "rank": 3,
        "study_time": 68.0
    },
    {
        "discord_user_id": 173816835082273743,
        "username": "oswcsocdcf",
        "rank": 4,
        "study_time": 68.0
    },
    {
        "discord_user_id": 863085665046287668,
        "username": "vrltvwdppx",
        "rank": 5,
        "study_time": 67.0
    },
    {
        "discord_user_id": 738628035617842786,
        "username": "xaedunnmzp",
        "rank": 6,
        "study_time": 67.0
    }
]
```

## userstats

Returns general information about a user.

Takes url args for user_id.

Example call:
```
http://localhost:5000/userstats/102484975215862243
```

Example response:

```
{
    "username": "bluzoosqbm",
    "stats": {
        "pastDay": {
            "rank": 61,
            "study_time": 7.0
        },
        "pastWeek": {
            "rank": 25,
            "study_time": 61.0
        },
        "pastMonth": {
            "rank": 185,
            "study_time": 39.0
        },
        "all_time": {
            "rank": 185,
            "study_time": 39.0
        },
        "average_per_day": 1.857,
        "currentStreak": 1,
        "longestStreak": 1
    },
    "roleInfo": {
        "role": {
            "hours": "20-40",
            "id": 666302147176169502,
            "name": "advanced (20-40h)",
            "mention": "<@&792781265542971409>"
        },
        "next_role": {
            "hours": "40-60",
            "id": 666302227484508170,
            "name": "expert (40-60h)",
            "mention": "<@&792781265542971410>"
        },
        "time_to_next_role": 1.0
    }
}
```

## usertimeseries

Returns time series data about a users study hours, and a list of neighbors.

Takes url args for user_id, and params for time_interval. Time interval must be one of "pastDay", "pastWeek", "pastMonth", "allTime".

Example call:
```
http://localhost:5000/usertimeseries/102484975215862243?time_interval=pastWeek
```

Example response:
```
{
    "timeseries": [
        {
            "date": "2021-02-21",
            "rank": 61,
            "study_time": 7.0
        },
        {
            "date": "2021-02-20",
            "rank": 52,
            "study_time": 7.0
        },
        {
            "date": "2021-02-19",
            "rank": 96,
            "study_time": 5.0
        },
        {
            "date": "2021-02-18",
            "rank": 123,
            "study_time": 4.0
        },
        {
            "date": "2021-02-17",
            "rank": 29,
            "study_time": 9.0
        },
        {
            "date": "2021-02-16",
            "rank": 43,
            "study_time": 8.0
        },
        {
            "date": "2021-02-15",
            "rank": 128,
            "study_time": 4.0
        }
    ],
    "neighbors": [
        {
            "discord_user_id": 518488332978841649,
            "username": "hzpgidkuwc",
            "rank": 20,
            "study_time": 63.0
        },
        {
            "discord_user_id": 228974702591634818,
            "username": "hgncxhevry",
            "rank": 21,
            "study_time": 63.0
        },
        {
            "discord_user_id": 217840426440527737,
            "username": "jbhyqdnnyi",
            "rank": 22,
            "study_time": 63.0
        },
        {
            "discord_user_id": 562511513199020028,
            "username": "tfluesqkql",
            "rank": 23,
            "study_time": 62.0
        },
        {
            "discord_user_id": 438011540564379889,
            "username": "oufvdmsunn",
            "rank": 24,
            "study_time": 62.0
        },
        {
            "discord_user_id": 991287113119009422,
            "username": "bluzoosqbm",
            "rank": 25,
            "study_time": 61.0
        },
        {
            "discord_user_id": 462229337138157709,
            "username": "supvclaxtz",
            "rank": 26,
            "study_time": 61.0
        },
        {
            "discord_user_id": 428869972841033146,
            "username": "joffmjarky",
            "rank": 27,
            "study_time": 61.0
        },
        {
            "discord_user_id": 737826033723676601,
            "username": "holkgvwiit",
            "rank": 28,
            "study_time": 60.0
        },
        {
            "discord_user_id": 182321490621867435,
            "username": "sllyuqouvf",
            "rank": 29,
            "study_time": 60.0
        },
        {
            "discord_user_id": 708366450576113731,
            "username": "krrxgzgtqo",
            "rank": 30,
            "study_time": 59.0
        }
    ]
}
```

# TODO

- Right now users are inserted into the database if they are queried and don't exist. Don't do this.
