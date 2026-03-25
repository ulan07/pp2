import os 
files = [f for f in os.listdir("dir1") if f.endswith(".txt")]
print(files)