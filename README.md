# JishoBot

![](https://github.com/Aetolis/JishoBot/blob/main/figs/JishoBot_logo.png)

**JishoBot** is a [Discord](https://discord.com/company) bot that allows users of the popular video and text communication service to search for the definitions, translations, stroke order, etc. of Japanese words via the `?search` command.

![](https://github.com/Aetolis/JishoBot/blob/main/figs/embed_example.png)

The bot responds to the `?search` command using an embed object that contains (when applicable), a hyperlink to the [Jisho.org page](https://jisho.org/word/%E6%96%87%E5%AD%A6) for the keyword, the english definition, the parts of speech, and hyperlinks a static image ([文](https://media.kanjialive.com/kanji_strokes/bun-fumi_4.svg)[学](https://media.kanjialive.com/kanji_strokes/mana(bu)_8.svg)) and stroke order animation ([文](https://media.kanjialive.com/kanji_animations/kanji_mp4/bun-fumi_00.mp4)[学](https://media.kanjialive.com/kanji_animations/kanji_mp4/mana(bu)_00.mp4)) for each individual kanji. The embed object was created to be as compact and intuitive as possible.

JishoBot is coded in Python and utilizes the [discord.py](https://discordpy.readthedocs.io/en/latest/) module/API wrapper for Discord. The Japanese language data is collected from the [Jisho.org](http://jisho.org/about) and the [Kanji Alive](https://app.kanjialive.com/api/docs) APIs.

When a user searches for a keyword or the keyword contains kanji that JishoBot has not encountered before, the nessecary data is collected from the Jisho.org and Kanji Alive APIs. JishoBot then subsequently stores the information in a normalized SQLite relational database.

![](https://github.com/Aetolis/JishoBot/blob/main/figs/db_diagram.png)

When an error occurs, JishoBot will print information about the error to the command line. In the event of resolvable errors, JishoBot has error handlers that will resolve such errors without crashing the program. On the other hand, for unresolvable errors, the program will exit with a status of 1.

The JishoBot_DF branch of this repository also contains another version of JishoBot, `JishoBot_DF.py` that stores data in a normalized tabular format using [pandas](https://pandas.pydata.org/about/) DataFrames instead of using SQLite.

## Requirements
JishoBot requires all dependant modules to be installed on the host computer. The program also requires there to be a `.env` file, in the same directory as `JishoBot.py`, with the following format:

```
# Environment Variables
bot_token = "INSERT DISCORD BOT TOKEN"
rapidapi_key = "INSERT KANJI ALIVE API KEY"
```

The `bot_token` can be obtained by creating a new application through the [Discord Developer Portal](https://discord.com/developers/applications), and the `rapidapi_key` through the [Rapid API](https://rapidapi.com/KanjiAlive/api/learn-to-read-and-write-japanese-kanji) landing page for Kanji Alive.

## Notes
To-do's and areas of improvement:
* Port source code from Python to Node.js.
* Migrate database from SQLite to a client-server database.
* Implement additional functionality like Google's [Translation API](https://cloud.google.com/translate/)
* Ability to search for synonyms
* Add links to audio recordings of vocabulary to embed object
* `?kanji` command that perhaps can scrape data from [#kanji Jisho.org webpage](https://jisho.org/search/%E6%96%87%E5%AD%A6%20%23kanji) using XPath.
