import datetime, tweepy, configparser
from tweepy.auth import AppAuthHandler

Config = configparser.ConfigParser()
Config.read("keys.ini")

APP_KEY = Config.get("API", "KEY")
APP_SECRET = Config.get("API", "SECRET")

"""
This class runs within a new thread each time
it actually is the one that makes the requests to the Twitter API.
"""

class Scraper:
    currentCount = 0

    def __init__(self, job, budget, db):
        self.job = job
        self.budget = budget
        self.db = db
        self.currentCount = self.db.CountDB.get(self.job.url)

    def updateCount(self):
        self.db.CountDB.set(self.job.url, currentCount)
        self.job.lastRun = datetime.datetime.now().isoformat()
        self.db.set(url, self.job.to_json())

    def run(self):
        self.auth = AppAuthHandler(APP_KEY, APP_SECRET)
        self.api = tweepy.API(self.auth)

        if not self.api:
            print("Error running job, could not authenticate")
            return
        print("authed with twitter")
