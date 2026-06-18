import math

n = 4
s = 25

area = (n * s * s) / (4 * math.tan(math.pi / n))

print("The area of the polygon is:", int(area))