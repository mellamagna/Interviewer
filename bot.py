# bot.py
import os

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

version = "1.0"
prefix = "!interview"
shortprefix = "!in"

threshold = 0.5

#####utility methods

def refresh_questions():
	with open("questions.json") as json_file:
		q = json.load(json_file)
	return q

#####runtime variables

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
	output += "!interview refresh - refreshes questions from internal 'questions.json' file (after manual replacement)\n"
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

def checkquestion(text, checks):
	t = text.lower()
	score = 0
	for x in checks:
		if re.search(x, t):
			score += 1
	return score

def checkscore(score, checks):
	if (score / len(checks)) > threshold:
		return True
	else:
		return False

def random_response():
	words = []
	words.append("Good!")
	return words[random.randint(0,len(words) - 1)]

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
		cardTitle = "Likely Correct"
		colorVar = 0x42f554
	else:
		await add_reaction_array(message, emojiarrayno())
		cardTitle = "Indeterminate"
		colorVar = 0xcfcfcf
	desc = "(" + str(score) + "/" + str(len(checks)) + " keywords matched)"
	embedVar = discord.Embed(title=cardTitle, description=desc, color=colorVar)
	embedVar.add_field(name="Example answer", value=q["answer"], inline=False)
	await message.channel.send(content=output, embed=embedVar)
	del(currentquestions[uid])

@client.event
async def on_message(message):
	if message.author == client.user:
		return
	elif message.content.startswith(prefix) or message.content.startswith(shortprefix):
		try:
			if message.content.startswith(shortprefix):
				args = message.content[len(shortprefix):len(message.content)].strip().split()
			else:
				args = message.content[len(prefix):len(message.content)].strip().split()
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
					questionbank = refresh_questions()
					await message.channel.send("Questions successfully loaded from the data file.")
				else:
					await message.channel.send(invinput())
			except ValueError:
				await message.channel.send(invinput())
			except IndexError:
				await message.channel.send(invinput())
		except IndexError:
			await assign_random_question(message)
	elif client.user.mentioned_in(message):
		print("Bot ping detected from user " + str(message.author.id))
		await assign_random_question(message)
	elif message.author.id in currentquestions:
		await evaluate_question(message)

client.run(TOKEN)