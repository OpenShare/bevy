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
        if not self.currentCount:
            self.currentCount = 0

    def updateCount(self):
        self.db.CountDB.set(self.job.url, self.currentCount)
        self.job.lastRun = datetime.datetime.now().isoformat()
        self.db.JobDB.set(self.job.url, self.job.to_json())

    def run(self):
        self.auth = AppAuthHandler(APP_KEY, APP_SECRET)
        self.api = tweepy.API(self.auth)

        if not self.api:
            print("Error running job, could not authenticate")
            return

        # Search for some tweets
        self.job.maxTweetID
        search_results = self.api.search(q=self.job.url, count=100 * self.budget, since_id=self.job.maxTweetID)
        addCount = len(search_results)
        if len == 0:
            return
        self.currentCount = int(self.currentCount) + addCount
        if addCount != 0:
            self.job.maxTweetID = search_results[0].id
        self.updateCount()
