class Eve:
    def b(self,m,a=0):
        while a<=m:
            yield a
            a+=12

            

a=int(input())
c=Eve()
for i in c.b(a):
    print(i,end=" ")
            


