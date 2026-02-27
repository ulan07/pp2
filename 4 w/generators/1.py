class Eve:
    def b(self,m):
        for i in range(0,m):
            yield i**2
            

a=int(input())
c=Eve()
for i in c.b(a):
    print(i,end=" ")
            


