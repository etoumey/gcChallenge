from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import getpass
import sqlite3
import datetime


class challenge:
  def __init__(self, url, participants):
    self.url = url
    self.participants = participants


def queryCredentials():
	cred = []
	username = input("Username: ")
	password = getpass.getpass(prompt='Password: ')

	cred.append(username + '\n')
	cred.append(password + '\n')

	print("Credentials sucessfully loaded...")
	return cred


def getUserPreferences():
	with open('challengeDetails.txt') as fid:
		url = fid.readline()
		participantsRaw = fid.readline()

	return challenge(url, participantsRaw.split(','))


def browserInit():
	# Set Firefox preferences 
	ffProfile = webdriver.FirefoxProfile()

	#Setup browser as headless
	opts = Options()
	opts.headless = True

	# Instantiate a Firefox browser object with the above-specified profile settings
	print("Browser preferences configured")
	browser = webdriver.Firefox(ffProfile, options = opts)
	print("Launching browser")

	return browser


def login(browser, credentials):
	browser.get('https://connect.garmin.com/modern')

	#input field is within an iframe
	element = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "gauth-widget-frame-gauth-widget")))
	frame = browser.find_element_by_id('gauth-widget-frame-gauth-widget')
	browser.switch_to.frame(frame)

	element = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "username")))

	#populate username and password
	try:
		usernameField = browser.find_element_by_id("username")
		usernameField.send_keys(credentials[0])
		element = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "password")))

		passwordField = browser.find_element_by_id("password")
		passwordField.send_keys(credentials[1])
		passwordField.submit()
	
		# Wait for login confirmation
		browser.switch_to.default_content()
		element = WebDriverWait(browser, 20).until(
			EC.element_to_be_clickable((By.XPATH, '/html/body/div/div[3]/header/div[1]/div'))
		)
		print("Login Success")

	except:
		print("Login Failure")


def getSteps(browser, challengeDetails):
	baseXpath = '/html/body/div/div[3]/div[2]/div[3]/div/div/div[2]/div[1]/div[2]/div/div[1]/div/div/ol/li['
	tailPersonXpath = ']/div[3]/span/a'
	tailStepsXpath = ']/div[4]'

	waitTime = 20
	person = [None] * len(challengeDetails.participants)
	steps = [None] * len(challengeDetails.participants)
	index = 0

	for people in challengeDetails.participants:
		personXpath = baseXpath + str(index+2) + tailPersonXpath
		stepsXpath = baseXpath + str(index+2) + tailStepsXpath
		personElement = WebDriverWait(browser, waitTime).until(
			EC.presence_of_element_located((By.XPATH, personXpath)))
		matchIndex = challengeDetails.participants.index(str(personElement.text))
		person[matchIndex] = str(personElement.text)
		stepElement = WebDriverWait(browser, waitTime).until(
			EC.presence_of_element_located((By.XPATH, stepsXpath)))
		steps[matchIndex] = stepElement.text
		index = index+1
	return steps


def databaseInit(challengeDetails):
	connection = sqlite3.connect('stepChallenge.db')
	# Basic create if doesn't already exist logic 
	middleString = ''
	for people in challengeDetails.participants:
		middleString = middleString + ' ' + people.replace(" ","") + ' text, '


	sqlCreateTable = 'CREATE TABLE IF NOT EXISTS steps (date text NOT NULL,' + middleString + ' PRIMARY KEY (date) );'	
	cursor = connection.cursor()
	cursor.execute(sqlCreateTable)
	return connection


def updateDatabase(db, steps, challengeDetails):
	cursor = db.cursor()

	middleString = ''
	endString = '?, '
	for people in challengeDetails.participants:
		if people != challengeDetails.participants[len(challengeDetails.participants)-1]:
			middleString = middleString + ' ' + people.replace(" ","") + ', '
			endString = endString + '?, '
		else:
			middleString = middleString + ' ' + people.replace(" ","") 
			endString = endString + '? '


	timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	steps.insert(0, timestamp)
	sqlUpdate = 'INSERT INTO steps(date, ' + middleString + ' ) VALUES(' + endString + ') '
	cursor.execute(sqlUpdate,  steps)
	db.commit()



cred = queryCredentials()
challengeDetails = getUserPreferences()
browser = browserInit()
login(browser, cred)
browser.get(challengeDetails.url)
steps = getSteps(browser, challengeDetails)
browser.quit()

db = databaseInit(challengeDetails)
updateDatabase(db, steps, challengeDetails)
db.close()

