import datetime, tweepy
from tweepy.auth import AppAuthHandler

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
        self.job.commit(self.db.JobDB)
        self.db.CountDB.set(self.job.url, self.currentCount)

    def run(self):
        # Lookup the keys of the URL owner
        ownerKey = self.db.Whitelist.get(self.job.url)
        keys = self.db.Users.get(ownerKey)

        if not keys:
            print("Can't run %s as it has no onwer!" % self.job.url)
            return

        keys = keys.decode('utf-8').split('|')
        self.auth = AppAuthHandler(keys[0], keys[1])
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
