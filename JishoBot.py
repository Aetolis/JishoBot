import os
import sys
import requests
import json
import io
import discord
import sqlite3
from sqlite3 import Error

from discord.ext import commands
from dotenv import load_dotenv

import unicodedata

# check if .env file exists in current directory
if not os.path.isfile(".env"):
    print("A .env file containing the Discord bot token and Kanji Alive API key is required!")
    sys.exit(1)
# load bot token and rapid API key from .env file
load_dotenv()
token = os.environ.get("bot_token")
rapidapi_key = os.environ.get("rapidapi_key")

def build_URL(host, resource_path, protocol="https"):
    """Build URL according to specified 'host', 'resource_path', and 'protocol'.
    """
    if resource_path[0] != '/':
        resource_path = '/' + resource_path
    return f"{protocol}://{host}{resource_path}"

def create_db(db_filepath):
    """Initializes sqlite3 database if it does not exist and returns connection object.
    """
    conn = None
    try:
        conn = sqlite3.connect(db_filepath)
        cur = conn.cursor()
        # create jisho_data table
        cur.execute("""CREATE TABLE IF NOT EXISTS jisho_data (
                     keyword text,
                     word text,
                     reading text,
                     parts_of_speech text,
                     english text,
                     jisho_link text,
                     CONSTRAINT jisho_pk PRIMARY KEY (keyword, word),
                     FOREIGN KEY (word) REFERENCES kanji_order (word))""")
        # create kanji_data table
        cur.execute("""CREATE TABLE IF NOT EXISTS kanji_data (
                     character text PRIMARY KEY,
                     image text,
                     stroke text,
                     FOREIGN KEY (character) REFERENCES kanji_order (character))""")
        # create kanji_order table
        cur.execute("""CREATE TABLE IF NOT EXISTS order_data (
                     word text,
                     character text,
                     kanji_order int,
                     CONSTRAINT order_pk PRIMARY KEY (word, character))""")
        # commit changes to database
        conn.commit()
    # exit program if connection to db can not be established
    except Error as db_error:
        print(db_error)
        sys.exit(1)
    return conn

def search_jisho(cur, keyword, index=0):
    """Searches Jisho API for keyword and applies changes to DB. Returns 'keyword' in Japanese or 'None' if search unsuccessful.
    """
    # determine page number according to 'index'
    page = index / 20 if index != 0 else 1
    # create parameters for GET request
    paramsD = {"keyword": f"\"{keyword}\"", "page": page}

    # issue GET request
    response = requests.get(build_URL("jisho.org", "/api/v1/search/words"), params=paramsD)
    # check status code and format of response
    if response.status_code != 200 or response.headers["Content-Type"] != "application/json; charset=utf-8":
        return None

    # parse response into json format
    data = response.json()["data"]
    # if search did not return any results
    if data == []:
        return None

    try:
        # avoiding Python format strings due to vulnerability to injection
        cur.execute("""INSERT INTO jisho_data
                     VALUES (?, ?, ?, ?, ?, ?)""",
                 (keyword, data[index]["slug"],
                  data[index]["japanese"][0]["reading"],
                  "; ".join(data[index]["senses"][0]["parts_of_speech"]),
                  "; ".join(data[index]["senses"][0]["english_definitions"]),
                  "https://jisho.org/word/{}".format(data[index]["slug"])))
    except Error as db_error:
        print(db_error)
        return None
    conn.commit()
    return data[index]["slug"]

def search_kanji(cur, keyword):
    """Searches the KanjiAlive API for each kanji component of 'keyword' and applies changes to DB. Returns 'None' keyword does not contain kanji.
    """
    # create header for GET request
    header = {"x-rapidapi-key": rapidapi_key, "x-rapidapi_host": "kanjialive-api.p.rapidapi.com"}
    # initialize order count
    count = 0

    # for each component of the keyword
    for i in range(len(keyword)):
        # if not hiragana and not katakana (keyword[i] is kanji)
        if not (ord(u"\u3041") <= ord(keyword[i]) <= ord(u"\u309F")) and not (ord(u"\u30A0") <= ord(keyword[i]) <= ord(u"\u30FF")):
            try:
                # check if kanji component already exists in kanji_data table
                cur.execute("""SELECT 1 FROM kanji_data WHERE character = ?""", (keyword[i],))
            except Error as db_error:
                print(db_error)

            # table entry does not exist, fetch data from Kanji Alive API
            if cur.fetchall() == []:
                # create URL for GET request
                url = build_URL("kanjialive-api.p.rapidapi.com", f"/api/public/kanji/{keyword[i]}")
                # issue GET request
                response = requests.get(url, headers=header)

                # if status code is not 200 or response is not in json format
                if response.status_code != 200 or response.headers["Content-Type"] != "application/json; charset=utf-8":
                    # on error continue to next component of 'keyword'
                    continue

                # parse response into json format
                data = response.json()
                # continue if API search did not return any results
                if data == {'error': 'No kanji found.'}:
                    print(f"Image and stroke order for {keyword[i]} not found in Kanji Alive API!")
                    continue

                # update database
                try:
                    cur.execute("""INSERT INTO kanji_data
                                 VALUES (?, ?, ?)""",
                             (keyword[i],
                              data["kanji"]["video"]["poster"],
                              data["kanji"]["video"]["mp4"]))
                    cur.execute("""INSERT INTO order_data
                                 VALUES (?, ?, ?)""",
                             (keyword,
                              keyword[i],
                              count))
                except Error as db_error:
                    print(db_error)
                count += 1

            # kanji already exists in kanji_data table
            else:
                # update order_data table for 'keyword'
                try:
                    cur.execute("""INSERT INTO order_data
                                 VALUES (?, ?, ?)""",
                             (keyword,
                              keyword[i],
                              count))
                except Error as db_error:
                    print(db_error)
                count += 1
    # if no kanji was found, return None
    if count == 0:
        return None
    conn.commit()
    return 0

def search_apis(cur, keyword, index=0):
    """Search Jisho and KanjiAlive API for 'keyword' and apply changes to DB. Returns 'None' if search fails.
    """
    # search Jisho API
    word = search_jisho(cur, keyword, index)
    # if search_jisho returned None, raise exception
    if word == None:
        raise Exception

    # check if order_data table already contains database
    # have to check this condition in the case of synonyms
    try:
        cur.execute("""SELECT 1 FROM order_data WHERE word = ?""", (word,))
    except Error as db_error:
        print(db_error)
    if cur.fetchall() == []:
        # search KanjiAlive API
        # possible for 'word' to not contain any kanji
        if search_kanji(cur, word) == None:
            print(f"{word} does not contain any kanji.")
    return 0

# establish connection with database
conn = create_db("db/JishoBot.db")

# the bot responsed to commands that are prefixed with a question mark
bot = commands.Bot(command_prefix='?')

# ?hello command
@bot.command(name="hello")
async def bot_say_hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

# ?search command
@bot.command(name="search")
async def bot_search_jisho(ctx, *, arg):
    # create cursor object for database queries
    cur = conn.cursor()

    # attempt to fetch keyword/str(arg) from jisho_data
    try:
        cur.execute("""SELECT * FROM jisho_data WHERE keyword = ?""", (str(arg),))
        jisho_row = cur.fetchone()
    except Error as db_error:
        print(db_error)

    # fetch data from APIs and update table if entry does not exist
    if jisho_row == None:
        try:
            search_apis(cur, str(arg))
            cur.execute("""SELECT * FROM jisho_data WHERE keyword = ?""", (str(arg),))
            jisho_row = cur.fetchone()
        except Error as db_error:
            print(db_error)
        except Exception:
            await ctx.send(f":x:**Jisho.org API failed to return result for \"{str(arg)}\"!**")

    # jisho_row column format is: (keyword(0), word(1), reading(2), parts_of_speech(3), english(4), jisho_link(5))
    try:
        cur.execute("""SELECT order_data.character, kanji_data.image, kanji_data.stroke
                     FROM order_data JOIN kanji_data
                     ON order_data.character = kanji_data.character
                     WHERE order_data.word = ?
                     ORDER BY order_data.kanji_order ASC""", (jisho_row[1],))
        kanji_rows = cur.fetchall()
    except Error as db_error:
        print(db_error)

    # create an embed object to send
    embed = discord.Embed(title="**Jisho Search**", colour=discord.Colour(0xffffff),
                          description="[**{}**](https://jisho.org/word/{})\n {}".format(jisho_row[1], jisho_row[1], jisho_row[2]))
    # add field for definition
    embed.add_field(name="English definition -", value=jisho_row[4], inline=False)
    # add field for parts of speech
    if jisho_row[3] != '':
        embed.add_field(name="Parts of speech -", value=jisho_row[3], inline=False)
    # if word contains kanji
    if kanji_rows != []:
        # add field for image and stroke order animation of kanji
        img_string, stroke_string = "", ""
        for i in range(len(kanji_rows)):
            img_string += "[{}]({})".format(kanji_rows[i][0], kanji_rows[i][1])
            stroke_string += "[{}]({})".format(kanji_rows[i][0], kanji_rows[i][2])
        embed.add_field(name="Images -", value=img_string, inline=False)
        embed.add_field(name="Stroke order -", value=stroke_string, inline=False)
    await ctx.send(embed=embed)

# local error handler for ?search
@bot_search_jisho.error
async def bot_search_jisho_handler(ctx, error):
    # if required argument is missing
    if isinstance(error, commands.MissingRequiredArgument):
        if error.param.name == 'arg':
            await ctx.send(":x:**Please specify a keyword!**")

# run bot
bot.run(token)
