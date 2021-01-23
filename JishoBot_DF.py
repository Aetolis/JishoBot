import os
import requests
import json
import io
import discord
import pandas as pd

from discord.ext import commands
from dotenv import load_dotenv

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

def search_jisho(keyword, index=0):
    """Searches Jisho API for keyword. Returns information about 'keyword' in a dict or 'None' if search unsuccessful.
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

    # format return data
    ret = {}
    ret["keyword"] = keyword
    ret["word"] = data[index]["slug"]
    ret["reading"] = data[index]["japanese"][0]["reading"]
    ret["parts_of_speech"] = "; ".join(data[index]["senses"][0]["parts_of_speech"])
    ret["english"] = "; ".join(data[index]["senses"][0]["english_definitions"])
    ret["jisho_link"] = "https://jisho.org/word/{}".format(ret["word"])
    return ret

def search_kanji(keyword):
    """Searches the KanjiAlive API for each component of 'keyword'. Returns DoL of links to images and mp4s of stroke order of 'keyword' componenets or 'None' if search unsuccessful.
    """
    kanji_data = []
    # create header for GET request
    header = {"x-rapidapi-key": rapidapi_key, "x-rapidapi_host": "kanjialive-api.p.rapidapi.com"}

    # for each component of the keyword
    for i in range(len(keyword)):
        # create URL for GET request
        url = build_URL("kanjialive-api.p.rapidapi.com", f"/api/public/kanji/{keyword[i]}")
        # issue GET request
        response = requests.get(url, headers=header)

        # check status code and response type
        if response.status_code != 200 or response.headers["Content-Type"] != "application/json; charset=utf-8":
            # on error continue to next component of 'keyword'
            continue

        # parse response into json format
        data = response.json()
        # if search did not return any results
        if data == {'error': 'No kanji found.'}:
            continue

        ret = {}
        ret["keyword"] = keyword
        # kanji component of keyword
        ret["kanji"] = keyword[i]
        # image of kanji
        ret["image"] = data["kanji"]["video"]["poster"]
        # mp4 of stroke order of kanji
        ret["stroke"] = data["kanji"]["video"]["mp4"]

        kanji_data.append(ret)

    # return None if search unsuccessful
    return kanji_data if kanji_data != [] else None

def search_apis(keyword, index=0):
    """Search Jisho and KanjiAlive API for 'keyword'. Returns results from both searches.
    """
    # search Jisho API
    jisho_data = search_jisho(keyword, index)
    # check if functions returned None
    if jisho_data == None:
        return None

    # search KanjiAlive API
    kanji_data = search_kanji(jisho_data["word"])
    if kanji_data == None:
        kanji_data = []

    return jisho_data, kanji_data


def update_df(jisho_df, kanji_df, keyword):
    """Searches for 'keyword' from both APIs and returns updated 'jisho_df' and 'kanji_df'.
    """
    # obtain API search results
    jisho_row, kanji_rows = search_apis(keyword)
    # return updated dataframes
    return jisho_df.append(jisho_row, ignore_index=True), kanji_df.append(kanji_rows, ignore_index=True)

def import_df(filename):
    """Imports 'filename' csv file from data directory and returns a dataframe. Returns None if file does not exist.
    """
    if not os.path.exists(f"exports/{filename}"):
        return None
    return pd.read_csv(f"exports/{filename}")

def export_df(jisho_df, kanji_df):
    """Export contents of 'jisho_df' and 'kanji_df' as a csv file to 'exports' directory. Create 'exports' directory if it does not exist.
    """
    if not os.path.exists("exports"):
        os.mkdir("exports")
    jisho_df.to_csv("exports/jisho_data.csv", index=False)
    kanji_df.to_csv("exports/kanji_data.csv", index=False)

# the bot responsed to commands that are prefixed with a question mark
bot = commands.Bot(command_prefix='?')

# ?hello command
@bot.command(name="hello")
async def bot_say_hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

# ?search command
@bot.command(name="search")
async def bot_search_jisho(ctx, *, arg):
    # import dataframes from .csv files
    jisho_df = import_df("jisho_data.csv")
    kanji_df = import_df("kanji_data.csv")
    # check that dataframes have been unsuccessfully imported
    if type(jisho_df) != pd.core.frame.DataFrame or type(kanji_df) != pd.core.frame.DataFrame:
        print("Could not import .csv file.\n")

    # check if the 'keyword' we are looking for already exists in the dataframe
    if str(arg) not in jisho_df.loc[:, "keyword"].values:
        # update the dataframe
        jisho_df, kanji_df = update_df(jisho_df, kanji_df, str(arg))
        # export updated dataframe
        export_df(jisho_df, kanji_df)

    # locate row with the 'keyword'
    jisho_data = jisho_df.loc[jisho_df["keyword"] == str(arg)]
    word = jisho_data.loc[:, ["word"]].values[0][0]

    # locate rows with 'word' kanji data
    kanji_data = kanji_df.loc[kanji_df["keyword"] == word].values if word in kanji_df.loc[:, "keyword"].values else []

    # create an embed object to send
    embed = discord.Embed(title="**Jisho Search**", colour=discord.Colour(0xffffff), description="[**{}**](https://jisho.org/word/{})\n {}".format(word, word, jisho_data.loc[:, ["reading"]].values[0][0]))
    # add field for definition
    embed.add_field(name="English definition -", value=jisho_data.loc[:, ["english"]].values[0][0], inline=False)
    # add field for parts of speech
    embed.add_field(name="Parts of speech -", value=jisho_data.loc[:, ["parts_of_speech"]].values[0][0], inline=False)
    # if kanji_data exists
    if len(kanji_data) != 0:
        # add field for image of kanji
        img_string = ""
        for i in range(len(kanji_data)):
            img_string += "[{}]({})".format(kanji_data[i][1], kanji_data[i][2])
        embed.add_field(name="Images -", value=img_string, inline=False)
        # add field for stroke order animation of kanji
        stroke_string = ""
        for i in range(len(kanji_data)):
            stroke_string += "[{}]({})".format(kanji_data[i][1], kanji_data[i][3])
        embed.add_field(name="Stroke order -", value=stroke_string, inline=False)
    await ctx.send(embed=embed)

# run bot
bot.run(token)
