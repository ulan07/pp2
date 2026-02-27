class Eve:
    def b(self,m):
        for i in range(0,m):
            if i%2==0:
                yield i
            

a=int(input())
c=Eve()
for i in c.b(a):
    print(i,end=",")
            


