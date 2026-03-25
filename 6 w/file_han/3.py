import os
if os.path.exists("sam.txt"):
    os.remove("sam.txt")
else:
    print("The file does not exist")