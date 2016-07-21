# import network libraries
import tornado.ioloop
import tornado.web

# other libraries
import json
import threading, time

# import local files
from database import Database
from scheduler import Job, Scheduler
from urllib.parse import urlparse

SORT_TIMEOUT = 300

# define the Database and Scheduler to be used
db = Database()
sc = Scheduler(db)

### Job Creation Endpoint
class JobCheck(tornado.web.RequestHandler):
    def createJob(self, url):
        newJob = Job(url)

        # new jobs take high priority
        newJob.commit(db.JobDB)

    def get(self):

        # Set headers
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")		

        # Try and grab the url they want to track and their API key
        url = self.get_argument('url')
        apiKey = self.get_argument('key')

        if url == "":
            self.set_status(400)
            return
        url = url.strip()
        apiKey = apiKey.strip()

        # Check the URL whitelist
        wlCheck = db.Whitelist.get(url)
        
        # This URL was not found in the whitelist database
        if not wlCheck:
            self.set_status(406, "URL Not Whitelisted")
            return

        # Check if the user owns this URL (URL against KEY)
        wlCheck = wlCheck.decode('utf-8')
        if wlCheck != apiKey:
            self.set_status(401, "URL and API Key Mismatch")
            return

        # Look up if a job is already in the database
        existingCheck = db.JobDB.get(url)
        parsedUrl = urlparse(url)
        if not parsedUrl.netloc:
            check = parsedUrl.path
        else:
            check = parsedUrl.netloc

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
