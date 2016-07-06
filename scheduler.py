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
        self.internalID = decoded['internalID']
        self.priority = decoded['priority']

"""
This class takes care of tracking rate limits as well as
Managing when certain tasks should be run.
"""
class Scheduler:
    def __init__(self, db):
        self.db = db

    def updatePriority(self, job, newPriority):
        # Update the priority in the database
        job.priority = newPriority
        self.db.JobDB.set(job.url, job.to_json())

    # Goes though each job in the database and evals the priority
    def sortJobs(self):
        print("[Scheduler] Sorting jobs...")
        # Grab all the jobs in the database
        jobs = []
        keys = self.db.JobDB.keys()

        # Collect jobs into
        for key in keys:
            url = key.decode('utf-8')
            value = self.db.JobDB.get(key)
            newJob = Job(url)
            newJob.from_json(url, value.decode('utf-8'))
            jobs.append(newJob)

        sortedJobs = []
        for job in jobs:
            count = self.db.CountDB.get(job.url)

            # Make sure to convert from Bytes
            if count:
                count = int(count)

            # If the job is brand new, then it needs to be done ASAP
            if not count:
                self.updatePriority(job, 2)
            # Counts more than 2k get a higher update rate
            elif count >= 2000:
                self.updatePriority(job, 1)
            # Counts any lower than this get updated less
            else:
                self.updatePriority(job, 0)
            # Push into list to sort
            sortedJobs.append(job)
        print("[Scheduler] Done sorting jobs")
        # Sort based on priority
        #sortedJobs.sort(key=lambda job: job.priority)
