import threading, dateutil.parser
from job import Job
from scraper import Scraper

NUM_REQS_PER_JOB_MAX_MIN = 10 # Max number of requests for low priority job
NUM_REQS_PER_JOB_MAX_MID = 20 # Max number of requests for medium priority jobs
NUM_REQS_PER_JOB_MAX_MAX = 40 # Max number of requests for highest priority jobs
NUM_REQS_MAX = 450

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

    def getJobs(self):
        # Grab all the jobs in the database
        jobs = []
        keys = self.db.JobDB.keys()

        # Collect jobs into
        for key in keys:
            url = key.decode('utf-8')
            newJob = Job(url)
            newJob.load(self.db.JobDB)
            jobs.append(newJob)

        return jobs

    # Goes though each job in the database and evals the priority
    def sortJobs(self):
        print("[Scheduler] Sorting jobs...")

        sortedJobs = []
        jobs = self.getJobs()

        for job in jobs:
            count = job.count

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
            count = job.count
            if count:
                count = int(count)

        # Sort by the time they were last run
        jobs.sort(key=lambda d: dateutil.parser.parse(d.lastRun))

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
                reqBudget = NUM_REQS_MAX - numRequests
                overbudget = True
            else:
                numRequests = numRequests + reqBudget
            print("Budget for %s is %d requests" % (runJob.url, reqBudget))
            self.spawnJob(runJob, reqBudget)
            if overbudget:
                print("[Scheduler] Out of requests to budget for this 15 minute window!")
                break

    def spawnJob(self, job, budget):
        scraperJob = Scraper(job, budget, self.db)
        spawnedThread = threading.Thread(target=scraperJob.run, args=())
        spawnedThread.start()
