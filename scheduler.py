import hashlib

"""
Jobs define run tasks for the Scheduler to run
"""
class Job:
    self.url = None
    self.internalID = None

    def __init__(self, url):
        self.url = url
        self.internalID = hashlib.sha224(url).hexdigest()

"""
This class takes care of tracking rate limits as well as
Managing when certain tasks should be run.
"""
class Scheduler:
    def __init__(self, db):
        self.db = db
