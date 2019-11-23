import time
import datetime
import hashlib

dayo = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
print hashlib.sha224("test_user%s" % dayo).hexdigest()
print dayo