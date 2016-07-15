# import network libraries
import tornado.ioloop
import tornado.web

# other libraries
import json
import threading, time

# import local files
from database import Database
from scheduler import Job, Scheduler

SORT_TIMEOUT = 300

# define the Database and Scheduler to be used
db = Database()
sc = Scheduler(db)

### Job Creation Endpoint
class JobCheck(tornado.web.RequestHandler):
    def createJob(self, url):
        newJob = Job(url)

        # new jobs take high priority
        newJob.priority = 2
        db.JobDB.set(url, newJob.to_json())

    def get(self):

        # Try and grab the url they want to track
        url = self.get_argument('url')
        if url == "":
            self.set_status(400)
            return
        url = url.strip()
        # Look up if a job is already in the database
        existingCheck = db.JobDB.get(url);

        # Set headers
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_status(200)

        # Assume everything is OK
        status = "OK"
        count = "0"

        # Only create one if we don't have an existing job
        if not existingCheck:
            self.createJob(url)
            # Send back a 202 for now, we are processing
            self.set_status(202)
            status = "Your job has been created, check back later for a count"

        else:
            # Do we have a count yet?
            countCheck = db.CountDB.get(url)

            if not countCheck:
                # No content for the count yet
                status = "Your job has not been processed yet"
            else:
                count = str(int(countCheck))

        # Return a formatted json responce
        res = "{\"status\": \"%s\", \"count\": %s}" % (status, count)
        self.write(res)

def sortTaskRunner():
    while True:
        sc.sortJobs()
        sc.runJobs()
        time.sleep(SORT_TIMEOUT)

def startWeb():
    #Kick off the HTTP server
    server = tornado.web.Application([
        (r"/job", JobCheck),
    ])
    server.listen(8880)
    tornado.ioloop.IOLoop.current().start()

def main():
    # Start a thread that will run the sorting of jobs
    scThread = threading.Thread(target=sortTaskRunner, args=())
    scThread.start()

    webThread = threading.Thread(target=startWeb, args=())
    webThread.start()

if __name__ == '__main__':
    main()
