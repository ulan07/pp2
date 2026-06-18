from functools import reduce
a=list(map(int,input().split()))
pos=list(filter(lambda x: x>=0,a))
print(pos)
tot=reduce(lambda x,y: x if x>y else y,pos)
print(tot)
for i,n in enumerate(a):
    print(i,n)
for i,n in zip(a,pos):
    print(i,n)