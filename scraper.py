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
        self.db.JobDB.set(self.job.url, self.job.to_json())

    def run(self):
        # Update last run datestamp
        self.job.lastRun = datetime.datetime.now().isoformat()
        self.db.JobDB.set(self.job.url, self.job.to_json())

        self.auth = AppAuthHandler(APP_KEY, APP_SECRET)
        self.api = tweepy.API(self.auth)

        if not self.api:
            print("Error running job, could not authenticate")
            return

        # Search for some tweets
        search_results = tweepy.Cursor(self.api.search, q=self.job.url, count=100, since_id=self.job.maxTweetID).pages(self.budget)

        addCount = 0
        for page in search_results:
            addCount = addCount + len(page)

        self.currentCount = int(self.currentCount) + addCount
        if addCount != 0:
            self.job.maxTweetID = page[0].id
        self.updateCount()
        print("%s finished running!" % self.job.url)
