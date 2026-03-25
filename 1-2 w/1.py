class person():
    def __init__(self,name,age):
        """initializes the person object"""
        self.name=name 
        self.age=age

ulan1 = person("Ulan",19)

l = ["a",1,2,"b",-6,-7]

l1 = list(filter(lambda x:isinstance(x,int) and x>0,l))

print(l1)