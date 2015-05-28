from refreshable import SafeRefreshableLoop
import time

# The test needs to be in a separate file because 
# the `__main__` module cannot be reloaded.

class Test(SafeRefreshableLoop):
    A = 0
    def __init__(self, x):
        self.A = 30
        self.x = x
        super(SafeRefreshableLoop, self).__init__()

    def b(self):
        self.x += self.A
        return self.A

    def step(self):
        print "hello", self.b(), self.x
        time.sleep(0.5)
        self.refresh()

