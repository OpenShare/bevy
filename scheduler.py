import hashlib, json, datetime
import dateutil.parser
from scraper import Scraper

NUM_REQS_PER_JOB_MAX_MIN = 10 # Max number of requests for low priority job
NUM_REQS_PER_JOB_MAX_MID = 20 # Max number of requests for medium priority jobs
NUM_REQS_PER_JOB_MAX_MAX = 40 # Max number of requests for highest priority jobs
NUM_REQS_MAX = 450

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
    lastRun = datetime.datetime.utcnow().isoformat()

    def __init__(self, url):
        self.url = url
        self.url = self.url.encode('utf-8')
        self.internalID = hashlib.sha224(self.url).hexdigest()

    def to_json(self):
        return json.dumps({'internalID': self.internalID, 'priority': self.priority, 'lastRun': self.lastRun, 'lastTweetID': self.lastTweetID})

    def from_json(self, newUrl, jsonStr):
        self.url = newUrl.encode('utf-8')
        decoded = json.loads(jsonStr)
        self.internalID = decoded['internalID']
        self.priority = decoded['priority']
        self.lastTweetID = decoded['lastTweetID']
        self.lastRun = decoded['lastRun']

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

    def getJobs(self):
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
        return jobs

    # Goes though each job in the database and evals the priority
    def sortJobs(self):
        print("[Scheduler] Sorting jobs...")

        sortedJobs = []
        jobs = self.getJobs()

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

    def runJobs(self):
        print("[Scheduler] RUNNING JOBS")
        jobs = self.getJobs()
        for job in jobs:
            count = self.db.CountDB.get(job.url)
            if count:
                count = int(count)

        # Sort by the time they were last run
        jobs.sort(key=lambda d: dateutil.parser.parse(job.lastRun))

        numRequests = 0
        overbudget = False
        for runJob in jobs:
            reqBudget = 0

            # Give the job a request budget based on priority
            if runJob.priority == 0:
                reqBudget = NUM_REQS_PER_JOB_MAX_MIN
            elif runJob.priority == 1:
                reqBudget = NUM_REQS_PER_JOB_MAX_MID
            else:
                reqBudget = NUM_REQS_PER_JOB_MAX_MAX

            # If we are about to go over budget then this is the last job we can process for now
            if (numRequests + reqBudget) >= NUM_REQS_MAX:
                reqBudget = numRequests - NUM_REQS_MAX
                overbudget = True
            else:
                numRequests = numRequests + reqBudget
            print("Budget for %s is %d requests" % (runJob.url, reqBudget))
            self.spawnJob(runJob, reqBudget)
            if overbudget:
                break;

    def spawnJob(self, job, budget):
        scraperJob = Scraper(job, budget, self.db)
        scraperJob.run()
