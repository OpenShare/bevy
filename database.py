import redis

class Database:
    CountDB = None
    JodDB = None

    def __init__(self):
        # Create a connection to the count database
        self.CountDB = redis.StrictRedis(host='localhost', port=6379, db=0)

        # Create another connection to the job queue database
        self.JobDB = redis.StrictRedis(host='localhost', port=6379, db=1)

        # Connection for the whitelist database
        self.Whitelist = redis.StrictRedis(host='localhost', port=6379, db=2)

        # Connection for user and twitter keys
        self.Users = redis.StrictRedis(host='localhost', port=6379, db=3)
