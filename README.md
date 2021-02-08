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
# add user with permissions to access studytogether db.
GRANT ALL PRIVILEGES on studytogether.* TO 'study_together'@'localhost';
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

There are three main queries:

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
        "rank": 1,
        "study_time": 70.0
    },
    {
        "discord_user_id": 927698802236956910,
        "rank": 2,
        "study_time": 68.0
    },
    {
        "discord_user_id": 290378422076173744,
        "rank": 3,
        "study_time": 68.0
    },
    {
        "discord_user_id": 173816835082273743,
        "rank": 4,
        "study_time": 68.0
    },
    {
        "discord_user_id": 863085665046287668,
        "rank": 5,
        "study_time": 67.0
    },
    {
        "discord_user_id": 738628035617842786,
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
    "stats": {
        "pastDay": {
            "rank": 100,
            "study_time": 6.0
        },
        "pastWeek": {
            "rank": 101,
            "study_time": 35.0
        },
        "pastMonth": {
            "rank": 94,
            "study_time": 154.0
        },
        "all_time": {
            "rank": 94,
            "study_time": 154.0
        },
        "average_per_day": 19.25,
        "currentStreak": 2,
        "longestStreak": 4
    },
    "roleInfo": {
        "role": {
            "hours": "120-160",
            "id": 672197498323861532,
            "name": "grandmaster (120-160h)",
            "mention": "<@&792781265547821087>"
        },
        "next_role": {
            "hours": "160-220",
            "id": 674297907150716959,
            "name": "study-machine (160-220h)",
            "mention": "<@&792781265547821088>"
        },
        "time_to_next_role": 6.0
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
    "timeseries": {
        "2021-02-07 17:00:00": {
            "rank": 100,
            "study_time": 6.0
        },
        "2021-02-06 17:00:00": {
            "rank": 177,
            "study_time": 2.0
        },
        "2021-02-05 17:00:00": {
            "rank": 17,
            "study_time": 10.0
        },
        "2021-02-04 17:00:00": {
            "rank": 145,
            "study_time": 4.0
        },
        "2021-02-03 17:00:00": {
            "rank": 210,
            "study_time": 0
        },
        "2021-02-02 17:00:00": {
            "rank": 170,
            "study_time": 2.0
        },
        "2021-02-01 17:00:00": {
            "rank": 200,
            "study_time": 1.0
        }
    },
    "neighbors": [
        {
            "discord_user_id": 932515466658138060,
            "rank": 96,
            "study_time": 35.0
        },
        {
            "discord_user_id": 862384702718551449,
            "rank": 97,
            "study_time": 35.0
        },
        {
            "discord_user_id": 668985024610717864,
            "rank": 98,
            "study_time": 35.0
        },
        {
            "discord_user_id": 438382606667001577,
            "rank": 99,
            "study_time": 35.0
        },
        {
            "discord_user_id": 194520434570021221,
            "rank": 100,
            "study_time": 35.0
        },
        {
            "discord_user_id": 102484975215862243,
            "rank": 101,
            "study_time": 35.0
        },
        {
            "discord_user_id": 954949519964969681,
            "rank": 102,
            "study_time": 34.0
        },
        {
            "discord_user_id": 916085044000758358,
            "rank": 103,
            "study_time": 34.0
        },
        {
            "discord_user_id": 820922041172774422,
            "rank": 104,
            "study_time": 34.0
        },
        {
            "discord_user_id": 723255456077380053,
            "rank": 105,
            "study_time": 34.0
        },
        {
            "discord_user_id": 376069723034697471,
            "rank": 106,
            "study_time": 34.0
        }
    ]
}
```

# TODO

- Right now users are inserted into the database if they are queried and don't exist. Don't do this.
