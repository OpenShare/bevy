# import network libraries
import tornado.ioloop
import tornado.web

# other libraries
import json

# import local files
from database import Database
from scheduler import Job, Scheduler

# define the Database and Scheduler to be used
db = Database()
sc = Scheduler(db)

### Job Creation Endpoint
class JobCheck(tornado.web.RequestHandler):
    def createJob(self, url):
        # TODO do something here
        db.JobDB.set(url, "pending")

    def get(self):

        # Try and grab the url they want to track
        url = self.get_argument('url')

        # Look up if a job is already in the database
        existingCheck = db.JobDB.get(url);

        # Only create one if we don't have an existing job
        if not existingCheck:
            self.createJob(url)

        # Send back a 202 for now, we are processing
        self.set_status(202)
        self.write("A job has been created for your URL. It may be a little while before results show up!")

def main():
    #Kick off the HTTP server
    server = tornado.web.Application([
        (r"/job", JobCheck),
    ])
    server.listen(8880)
    tornado.ioloop.IOLoop.current().start()

if __name__ == '__main__':
    main()
