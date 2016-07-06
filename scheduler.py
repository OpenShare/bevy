import hashlib, json, datetime

"""
Jobs define run tasks for the Scheduler to run
"""
class Job:
    url = None
    internalID = None

    # Priority -1 = Not set
    # Priority 0 = Can be done whenever
    # Priority 1 = Should be done ASAP
    # Priority 2 = Do first, before any other job
    priority = -1

    lastTweetID = 0
    lastChecked = None

    def __init__(self, url):
        self.url = url
        self.url = self.url.encode('utf-8')
        self.internalID = hashlib.sha224(self.url).hexdigest()

    def to_json(self):
        return json.dumps({'internalID': self.internalID, 'priority': self.priority})

    def from_json(self, newUrl, jsonStr):
        self.url = newUrl.encode('utf-8')
        decoded = json.loads(jsonStr)
        print(decoded)

"""
This class takes care of tracking rate limits as well as
Managing when certain tasks should be run.
"""
class Scheduler:
    def __init__(self, db):
        self.db = db
