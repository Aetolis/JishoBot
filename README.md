# JishoBot

![](https://github.com/Aetolis/JishoBot/blob/main/figs/JishoBot_logo.png)

**This version of JishoBot, `JishoBot_DF.py`, stores data in a normalized tabular format using pandas DataFrames. For the most up to date version of JishoBot, please refer to the main branch of the repository.**

**JishoBot** is a [Discord](https://discord.com/company) bot that allows users of the popular video and text communication service to search for the definitions, translations, stroke order, etc. of Japanese words via the `?search` command.

![](https://github.com/Aetolis/JishoBot/blob/main/figs/embed_example.png)

The bot responds to the `?search` command using an embed object that contains (when applicable), a hyperlink to the [Jisho.org page](https://jisho.org/word/%E6%96%87%E5%AD%A6) for the keyword, the english definition, the parts of speech, and hyperlinks a static image ([文](https://media.kanjialive.com/kanji_strokes/bun-fumi_4.svg)[学](https://media.kanjialive.com/kanji_strokes/mana(bu)_8.svg)) and stroke order animation ([文](https://media.kanjialive.com/kanji_animations/kanji_mp4/bun-fumi_00.mp4)[学](https://media.kanjialive.com/kanji_animations/kanji_mp4/mana(bu)_00.mp4)) for each individual kanji. The embed object was created to be as compact and intuitive as possible.

JishoBot is coded in Python and utilizes the [discord.py](https://discordpy.readthedocs.io/en/latest/) module/API wrapper for Discord. The Japanese language data is collected from the [Jisho.org](http://jisho.org/about) and the [Kanji Alive](https://app.kanjialive.com/api/docs) APIs.

When a user searches for a keyword or the keyword contains kanji that JishoBot has not encountered before, the nessecary data is collected from the Jisho.org and Kanji Alive APIs. JishoBot then subsequently stores the information in several normalized pandas DataFrames, which can be found in the `exports` directory as .csv files.

![](https://github.com/Aetolis/JishoBot/blob/main/figs/jisho_data.png)

![](https://github.com/Aetolis/JishoBot/blob/main/figs/kanji_data.png)

This method of storing the data is flawed because in the case where there are different keywords that contain the same kanji, the kanji data is duplicated. The version of JishoBot in the main branch of this repository resolves this flaw.

When an error occurs, JishoBot will print information about the error to the command line. In the event of resolvable errors, JishoBot has error handlers that will resolve such errors without crashing the program. On the other hand, for unresolvable errors, the program will exit with a status of 1.

## Requirements
JishoBot requires all dependant modules to be installed on the host computer. The program also requires there to be a `.env` file, in the same directory as `JishoBot.py`, with the following format:

```
# Environment Variables
bot_token = "INSERT DISCORD BOT TOKEN"
rapidapi_key = "INSERT KANJI ALIVE API KEY"
```

The `bot_token` can be obtained by creating a new application through the [Discord Developer Portal](https://discord.com/developers/applications), and the `rapidapi_key` through the [Rapid API](https://rapidapi.com/KanjiAlive/api/learn-to-read-and-write-japanese-kanji) landing page for Kanji Alive.
