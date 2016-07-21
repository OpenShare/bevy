import json, time, hashlib

"""
Jobs define run tasks for the Scheduler to run
"""
class Job:

    url = None
    internalID = None
    count = 0
    maxTweetID = 0

    def __init__(self, url):
        self.url = url
        self.url = self.url.encode('utf-8')
        self.internalID = hashlib.sha224(self.url).hexdigest()

    def to_json(self):
        return json.dumps({'internalID': self.internalID, 'maxTweetID': self.maxTweetID})

    def from_json(self, jsonStr):
        decoded = json.loads(jsonStr)
        self.internalID = decoded['internalID']
        self.maxTweetID = decoded['maxTweetID']

    def commit(self, db):
        # Commit to the database
        db.set(self.url, self.to_json())

        # Set score to the current timestamp (the last time this was run)
        db.zadd("timestamp", float(time.time()), self.url)

    def load(self, db):
        json_data = db.get(self.url)
        self.from_json(json_data.decode('utf-8'))
