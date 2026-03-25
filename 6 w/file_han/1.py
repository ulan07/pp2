with open("ex.txt","w",encoding="utf-8") as f:
    f.write("SOMETHING\n")
    f.write("something")
with open("ex.txt","r",encoding="utf-8") as f:
    print(f.read())
with open("ex.txt", "a", encoding="utf-8") as f:
    f.write("New line 1\n")
    f.write("New line 2")

with open("ex.txt", "r", encoding="utf-8") as f:
    print(f.read())