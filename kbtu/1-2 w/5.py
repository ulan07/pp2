import math
class c:
    def __init__(self, r):
        self.r=r
    def rfd(self):
        return math.pi*self.r**2
n=int(input())
circle = c(n)
print(f"{circle.rfd():.2f}")   #