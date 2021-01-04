# bot.py
import os
from os import path

import discord
from discord.utils import get
from dotenv import load_dotenv

import re
import random

import json

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()
discordclient = client

#####config (constants)

version = "1.1"
prefix = "!interview"
shortprefix = "!in"

questionfile = "questions.json"
scoreboardfile = "scoreboard.json"

#####utility methods

def refresh_userscores():
	if path.isfile(scoreboardfile):
		with open(scoreboardfile) as json_file:
			s = json.load(json_file)
		return s
	else:
		return {}

def refresh_questions():
	with open(questionfile) as json_file:
		q = json.load(json_file)
	return q

#####runtime variables

userscores = refresh_userscores()
currentquestions = {}
questionbank = refresh_questions()

#####discord actions

def helpmsg():
	output = ""
	output += "```"
	output += "FOR GENERAL USE: @mention me for a random interview question!\n"
	output += "I will then try to figure out whether or not your answer was correct via regex.\n"
	output += "I keep track of which user was given what question!\n"
	output += "\n"
	output += "Bot prefix: !interview (short form: !in)\n"
	output += "\n"
	output += "!interview refresh [questions|scores] - refreshes either the questions or scoreboard from the respective JSON files\n"
	output += "\n"
	output += "!interview about - displays general info about this bot\n"
	output += "!interview changelog - displays changes from last version\n"
	output += "!interview help - displays this message\n"
	output += "```"
	return output

def aboutmsg():
	output = ""
	output += "```"
	output += "Interviewer (v"
	output += version
	output += ")\n"
	output += "Asks interview questions related to full-stack Java.\n"
	output += "Written by Mel Lamagna\n"
	output += "```"
	return output

def changelog():
	output = ""
	output += "```"
	output += "v"
	output += version
	output += ":\n"
	output += "\t - initial things\n"
	output += "```"
	return output

def invinput():
	output = "Invalid command, please see `!interview help` for a list of available commands"
	return output

#####custom actions

def checkeveryone(text):
	t = text.lower()
	if re.search("@everyone", t) or re.search("@here", t):
		return True
	else:
		return False

def checkquestion(text, checks):
	t = text.lower()
	score = 0
	for x in checks:
		if re.search(r"\b{}(s)?\b".format(x), t):
			score += 1
	return score

def checkscore(score, checks):
	if (score / len(checks)) >= threshold_function():
		return True
	else:
		return False

def threshold_function(x):
#	return 0.4
	return 0.6 * pow(0.8, x)

def random_congrats():
	words = []
	words.append("Good!")
	words.append("Awesome!")
	words.append("Excellent!")
	words.append("Fantastic!")
	words.append("Nice job!")
	words.append("Great work!")
	return words[random.randint(0,len(words) - 1)]

def write_scores():
	with open(scoreboardfile, 'w', encoding='utf-8') as f:
		json.dump(userscores, f, ensure_ascii=False, indent=4)

def incr_userscore(uid):
	if not(str(uid) in userscores):
		userscores[str(uid)] = 1
	else:
		userscores[str(uid)] += 1
	write_scores()

def get_userscore(uid):
	return userscores[str(uid)]

#####emoji arrays

def emojiarrayyes():
	emojis = []
	emojis.append('\U00002714')
	return emojis

def emojiarrayno():
	emojis = []
	emojis.append('\U00002753')
	return emojis

def emojiarraybulb():
	emojis = []
	emojis.append('\U0001F4A1')
	return emojis

#####client events

@client.event
async def on_ready():
	await client.change_presence(activity=discord.Game('!interview help'))
	for guild in client.guilds:
		if guild.name == GUILD:
			break

	print(
        f'{client.user} is connected to the following guild:\n'
    	f'{guild.name}(id: {guild.id})'
    )

async def add_reaction_array(message, arr):
	for emoji in arr:
		await message.add_reaction(emoji)

async def add_custom_reaction(message, emojiname):
	emoji = discord.utils.get(message.guild.emojis, name=emojiname)
	if emoji:
		await message.add_reaction(emoji)

def userquestion(userid):
	return questionbank[currentquestions[userid]]

async def assign_random_question(message):
	uid = message.author.id
	randomquestion = random.randint(0,len(questionbank) - 1)
	currentquestions[uid] = randomquestion
	q = userquestion(uid)
	await add_reaction_array(message, emojiarraybulb())
	output = "<@" + str(uid) + ">, this is your assigned question:"
	questionTitle = "Question #" + str(q["id"])
	embedVar = discord.Embed(title=questionTitle, description=q["question"], color=0xd142f5)
	await message.channel.send(content=output, embed=embedVar)

async def evaluate_question(message):
	uid = message.author.id
	q = userquestion(uid)
	checks = q["checks"]
	score = checkquestion(message.content, checks)
	output = "<@" + str(uid) + ">, your answer is:"
	if checkscore(score, checks):
		await add_reaction_array(message, emojiarrayyes())
		incr_userscore(uid)
		cardTitle = "Likely Correct"
		colorVar = 0x42f554
	else:
		await add_reaction_array(message, emojiarrayno())
		cardTitle = "Indeterminate"
		colorVar = 0xcfcfcf
	desc = "(" + str(score) + "/" + str(len(checks)) + " keywords matched)"
	embedVar = discord.Embed(title=cardTitle, description=desc, color=colorVar)
	embedVar.add_field(name="Example answer", value=q["answer"], inline=False)
	if checkscore(score, checks):
		newtotal = "You now have **" + str(get_userscore(uid)) + "** correct answer(s)!"
		embedVar.add_field(name=random_congrats(), value=newtotal, inline=False)
	await message.channel.send(content=output, embed=embedVar)
	del(currentquestions[uid])

@client.event
async def on_message(message):
	if message.author == client.user:
		return
	elif message.content.startswith(prefix) or message.content.startswith(shortprefix):
		try:
			if message.content.startswith(prefix):
				args = message.content[len(prefix):len(message.content)].strip().split()
			else:
				args = message.content[len(shortprefix):len(message.content)].strip().split()
			command = args[0]
			args = args[1:len(args)]
			try:
				if command == "about":
					await message.channel.send(aboutmsg())
				elif command == "changelog":
					await message.channel.send(changelog())
				elif command == "help":
					await message.channel.send(helpmsg())
				elif command == "refresh":
					if args[0] == "questions":
						questionbank = refresh_questions()
						await message.channel.send("Questions successfully refreshed from `" + questionfile + "`")
					elif args[0] == "scores":
						userscores = refresh_scores()
						await message.channel.send("User scores successfully refreshed from `" + scoreboardfile + "`")
					else:
						await message.channel.send(invinput())
				elif command == "resetscores":
					userscores = {}
					await message.channel.send("User scores successfully reset.")
				else:
					await message.channel.send(invinput())
			except ValueError:
				await message.channel.send(invinput())
			except IndexError:
				await message.channel.send(invinput())
		except IndexError:
			await assign_random_question(message)
	elif client.user.mentioned_in(message) and not(checkeveryone(message.content)):
		print("Bot ping detected from user " + str(message.author.id))
		await assign_random_question(message)
	elif message.author.id in currentquestions:
		await evaluate_question(message)

client.run(TOKEN)