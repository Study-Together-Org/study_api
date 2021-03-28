# Study Together Api

This is a quart api for querying data related to study together.

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

This will run migrations and then insert fake data into the mysql and redis dbs (warning this will reset the dbs).
```bash
# install dependencies
pipenv install
# activate the environment
pipenv shell
# run insert_fake_data
python insert_fake_data.py
```

5. Start the Api

This will start the quart api on port 5000.
```bash
# activate the environment
pipenv shell
# start the bot
python bot.py & 
# start the quart api
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

Takes a param for match. The list of users will be searched by the glob `f"*{match}"`.

Example call:

```
http://localhost:5000/users?match=cole
```

Example response:

```
[
    {
        "discord_user_id": "619663424812613662",
        "tag": "#3088",
        "username": "Cole Killian"
    },
    {
        "discord_user_id": "294865385780412416",
        "tag": "#8220",
        "username": "Coleman"
    },
    {
        "discord_user_id": "687847542041608192",
        "tag": "#4048",
        "username": "Cole Fluet"
    },
    {
        "discord_user_id": "400866823643332608",
        "tag": "#0711",
        "username": "coleus"
    },
    {
        "discord_user_id": "254251545837699072",
        "tag": "#4408",
        "username": "Colean"
    }
]
```


## leaderboard

Returns leaderboard information on a time interval and the number of users in the server.

Takes params for offset, limit, and time_interval. Time interval must be one of "pastDay", "pastWeek", "pastMonth", "allTime".

Example call: 
```
http://localhost:5000/leaderboard?offset=0&limit=5&time_interval=pastWeek
```

Example response:

```
{
    "leaderboard": [
        {
            "discord_user_id": "724579964007219221",
            "rank": 1,
            "study_time": 112,
            "username": "saberscientist"
        },
        {
            "discord_user_id": "716376818072027167",
            "rank": 2,
            "study_time": 112,
            "username": "Bot of Discord"
        },
        {
            "discord_user_id": "708711987911065663",
            "rank": 3,
            "study_time": 112,
            "username": "Sadaf"
        },
        {
            "discord_user_id": "683017009889411242",
            "rank": 4,
            "study_time": 112,
            "username": "Discord User"
        },
        {
            "discord_user_id": "578536678961053716",
            "rank": 5,
            "study_time": 112,
            "username": "reedo"
        },
        {
            "discord_user_id": "494580308415348754",
            "rank": 6,
            "study_time": 112,
            "username": "Unturneddaddy"
        }
    ],
    "num_users": 30625
}
```

## userstats

Returns general information about a user.

Takes url args for user_id.

Example call:
```
http://localhost:5000/userstats/619663424812613662
```

Example response:

```
{
    "roleInfo": {
        "next_role": {
            "hours": "220-350",
            "id": 676158518956654612,
            "mention": "<@&792781265547821089>",
            "name": "study master (220-350h+)"
        },
        "role": {
            "hours": "160-220",
            "id": 674297907150716959,
            "mention": "<@&792781265547821088>",
            "name": "study-machine (160-220h)"
        },
        "time_to_next_role": 44.3
    },
    "stats": {
        "all_time": {
            "rank": 18463,
            "study_time": 175.7
        },
        "average_per_day": 7.321,
        "currentStreak": 3,
        "longestStreak": 5,
        "pastDay": {
            "rank": 6461,
            "study_time": 12.6
        },
        "pastMonth": {
            "rank": 18463,
            "study_time": 175.7
        },
        "pastWeek": {
            "rank": 19701,
            "study_time": 40
        }
    },
    "username": "Cole Killian"
}
```

## usertimeseries

Returns time series data about a users study hours, and a list of neighbors.

Takes url args for user_id, and params for time_interval. Time interval must be one of "pastDay", "pastWeek", "pastMonth", "allTime".

Example call:
```
http://localhost:5000/usertimeseries/619663424812613662?time_interval=pastWeek
```

Example response:
```
{
    "neighbors": [
        {
            "discord_user_id": "135465783089168384",
            "rank": 19696,
            "study_time": 40.1,
            "username": "bboc"
        },
        {
            "discord_user_id": "758651227302526976",
            "rank": 19697,
            "study_time": 40,
            "username": "wilbur | offline | exams"
        },
        {
            "discord_user_id": "754617725225140234",
            "rank": 19698,
            "study_time": 40,
            "username": "Synrr."
        },
        {
            "discord_user_id": "753854331500888154",
            "rank": 19699,
            "study_time": 40,
            "username": "Gangu"
        },
        {
            "discord_user_id": "707024839159971841",
            "rank": 19700,
            "study_time": 40,
            "username": "Cupica"
        },
        {
            "discord_user_id": "619663424812613662",
            "rank": 19701,
            "study_time": 40,
            "username": "Cole Killian"
        },
        {
            "discord_user_id": "519275513156730927",
            "rank": 19702,
            "study_time": 40,
            "username": "r33nter"
        },
        {
            "discord_user_id": "494498561099300865",
            "rank": 19703,
            "study_time": 40,
            "username": "rozetup"
        },
        {
            "discord_user_id": "476099239848575007",
            "rank": 19704,
            "study_time": 40,
            "username": "sudo rm -rf / --no-preserve-root"
        },
        {
            "discord_user_id": "471181139093094400",
            "rank": 19705,
            "study_time": 40,
            "username": "🌸⌬天桜（あまざくら）.py☭"
        },
        {
            "discord_user_id": "467451098735837186",
            "rank": 19706,
            "study_time": 40,
            "username": "CaptainVietnam6"
        }
    ],
    "timeseries": [
        {
            "date": "2021-03-17",
            "rank": 17100,
            "study_time": 7
        },
        {
            "date": "2021-03-18",
            "rank": 18619,
            "study_time": 6.3
        },
        {
            "date": "2021-03-19",
            "rank": 3467,
            "study_time": 14.2
        },
        {
            "date": "2021-03-20",
            "rank": 8618,
            "study_time": 11.5
        },
        {
            "date": "2021-03-21",
            "rank": 17356,
            "study_time": 6.8
        },
        {
            "date": "2021-03-22",
            "rank": 24330,
            "study_time": 3.2
        },
        {
            "date": "2021-03-23",
            "rank": 6461,
            "study_time": 12.6
        }
    ]
}
```
