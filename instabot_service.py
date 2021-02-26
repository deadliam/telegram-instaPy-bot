#!/usr/bin/env python3

import subprocess
import telebot
import os
import signal
import json
import psutil
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

working_dir = "/home/pi/Instagram"
bot_name = "instabot_runner"
logs_path = "/home/pi/InstaPy/logs"
general_log_name = "general.log"

# import RPi.GPIO as GPIO

# GPIO.setmode(GPIO.BOARD)
# # set up GPIO output channel
# GPIO.setup(11, GPIO.OUT)

TELEGRAM_TOKEN = "<TOKEN>"

bot = telebot.TeleBot(TELEGRAM_TOKEN)
pid = ""
currentActiveAccountName = ""


def startInstagramBot(arg):
	print("Account: " + arg)
	# GPIO.output(pin,GPIO.HIGH)

	botProcess = subprocess.Popen(['/usr/bin/python3', working_dir + '/' + bot_name + '.py', arg])
	out, err = botProcess.communicate()
	# print(out, err)
	pid = botProcess.pid
	# print(pid)
	while botProcess.poll() is None:
		time.sleep(0.5)
	
	if out is not None:
		if "CRITICAL" in out:
			return "CRITICAL"

	if botProcess.returncode is not 0:
		return str(botProcess.returncode)
	return "0"


def stopInstagramBot(pid):
	p = psutil.Process(pid)
	p.terminate()


def checkAlreadyRunningBot(name):
	process = subprocess.Popen(['ps', '-aef'], stdout=subprocess.PIPE)
	out, err = process.communicate()
	for p in out.splitlines():
		if name in str(p):
			pid = str(p.decode('utf-8')).split()[1]
			return True, int(pid)
	return False, None


def getStatus(name):
	accounts = readConfig()
	accountsNames = []
	for account in accounts:
		accountsNames.append(account["username"])
	statsList, dateTime = parseLog(name)
	return statsList, dateTime


def parseLog(account_name):
	log_path = logs_path + "/" + account_name + "/" + general_log_name
	resultList = []
	dateTime = ""

	with open(log_path, 'r') as file_:
		line_list = list(file_)
		line_list.reverse()

		count = 0
		for line in line_list:

			if line.find('Sessional Live Report:') != -1:
				dateStr = line.split()
				dateTime = dateStr[1] + " " + dateStr[2]

			if count > 0:
				break

			if line.find('|> No any statistics to show') != -1:
				resultList.append(line)
				count += 1

			if line.find('Unable to login to Instagram! You will find more information in the logs above.') != -1:
				resultList.append(line)

			if line.find('Internet Connection Status: error') != -1:
				count += 1
				resultList.append(line)
				return resultList

			if line.find('|> LIKED') != -1 and 'ALREADY LIKED:' in line:
				count += 1
				resultList.append(line)

			if line.find('|> COMMENTED') != -1:
				resultList.append(line)

			if line.find('|> FOLLOWED') != -1:
				resultList.append(line)
				
			if line.find('|> UNFOLLOWED') != -1:
				resultList.append(line)

			if line.find('|> LIKED') != -1 and 'comments' in line:
				resultList.append(line)

			if line.find('|> REPLIED to') != -1:
				resultList.append(line)

			if line.find('|> INAPPROPRIATE') != -1:
				resultList.append(line)

			if line.find('|> NOT VALID') != -1:
				resultList.append(line)

			if line.find('|> WATCHED') != -1:
				resultList.append(line)

			if line.find('On session start was FOLLOWING') != -1:
				resultList.append(line)

			if line.find('[Session lasted') != -1:
				resultList.append(line)

	return resultList, dateTime


def parseLogProgress(account_name):
	log_path = logs_path + "/" + account_name + "/" + general_log_name
	percentTag = 0
	percentLike = 0

	with open(log_path, 'r') as file_:
		line_list = list(file_)
		line_list.reverse()

		tagFlag = False
		likeFlag = False

		tagsStr = ""
		likesStr = ""

		lastSessionIsNotSuccess = False
		# delta = 0

		for line in line_list:
			if tagFlag and likeFlag:
				break
			
			if line.find('Session started!') != -1 or line.find('Session ended!') != -1 or lastSessionIsNotSuccess:
				tagFlag = True
				likeFlag = True

			if line.find('Like# [') != -1:
				resLike = line.split()[-1]
				likesStr = resLike
				resLike = re.match(r"[^[]*\[([^]]*)\]", resLike).groups()[0]
				firstLike = resLike.split("/")[0]
				secondLike = resLike.split("/")[1]
				if firstLike == secondLike:
					lastSessionIsNotSuccess = True
			
			if line.find('Tag [') != -1:
				resTag = line.split()[-1]
				tagsStr = resTag
				# delta = 10

	# percent = (int(percentTag) - delta + int(percentLike) * 0.1)
	# return percent
	return tagsStr, likesStr

def readConfig():
	with open(working_dir + '/config.json', 'r') as myfile:
		data=myfile.read()
		obj = json.loads(data)
		return obj['accounts']


def gen_markup(accountsNamesList):
	markup = InlineKeyboardMarkup()
	# markup.row_width = 5
	for name in accountsNamesList:
		markup.add(InlineKeyboardButton(name, callback_data=name))
	markup.add(InlineKeyboardButton("Status", callback_data="status"))
	markup.add(InlineKeyboardButton("Progress", callback_data="progress"))
	markup.add(InlineKeyboardButton("Stop", callback_data="stop"))
	return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
	
	global currentActiveAccountName
	acc = ""
	accounts = readConfig()
	accountsNames = []
	for account in accounts:
		accountsNames.append(account["username"])

	isRunning, pid = checkAlreadyRunningBot(bot_name)

	if call.data == "progress":

		if not isRunning:
			bot.answer_callback_query(call.id, "Bot is not running!")
			return

		tagsStr, likesStr = parseLogProgress(currentActiveAccountName)
		if isRunning and tagsStr == "" and likesStr == "":
			bot.answer_callback_query(call.id, "Loading... Try later!")
			return

		likes = ""
		if likesStr != "":
			likes = "\n" + likesStr + " LIKES"

		bot.send_message(call.message.chat.id, tagsStr + " TAGS" + likes)
		return

	if call.data == "status":
		# "ps -aef | grep -i 'instabot_runner' | grep -v 'grep'"

		for account in accounts:
			statsList, dateTime = getStatus(account["username"])
			statsList.insert(0, dateTime + "\n")
			statsList.insert(0, "=== " + account["username"] + " ===\n")
			stringStats = ''.join(statsList)
			bot.send_message(call.message.chat.id, stringStats)
		return

	if call.data == "stop":
		bot.answer_callback_query(call.id, "InstaBot stopped!")
		if isRunning:
			stopInstagramBot(pid)
		return

	if isRunning:
		bot.answer_callback_query(call.id, "Bot has already started!")
		return

	if call.data == "all":
		pass
		# Disabled button
		# bot.answer_callback_query(call.id, "All Accounts started!")

	count = 0
	for name in accountsNames:
		if call.data == name:
			currentActiveAccountName = str(accountsNames[count])
		count += 1

	bot.send_message(call.message.chat.id, currentActiveAccountName + " - has strated!")
	output = startInstagramBot(currentActiveAccountName)

	if output == "0":
		bot.send_message(call.message.chat.id, "--- Session ended ---")
	elif int(output) != 0:
		if int(output) == -15:
			bot.send_message(call.message.chat.id, "--- Session stopped by user ---")
			return
		bot.send_message(call.message.chat.id, "Execution failed with CODE = " + output)
	elif output == "CRITICAL":
		bot.send_message(call.message.chat.id, "--- CRITICAL execution failed --- \n Check statistics")


@bot.message_handler(func=lambda message: True)
def message_handler(message):

	accounts = readConfig()
	accountsNames = []
	for account in accounts:
		accountsNames.append(account["username"])

	bot.send_message(message.chat.id, "Select option:", reply_markup=gen_markup(accountsNames))


bot.polling(none_stop=True)
