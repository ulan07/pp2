import re 
import json

with open("raw.txt","r", encoding="utf-8") as f:
    txt=f.read()

price=re.findall(r"Стоимость\s*\n([\d\s,]+)",txt)

name=re.findall(r"\d+\.\n(.+)",txt)

total=re.search(r"ИТОГО:\s*\n([\d\s\,]+)",txt)

date=re.search(r"\d{2}\.\d{2}\.\d{4} \d{2}\:\d{2}:\d{2}",txt)

method=re.search(r"Банковская карта|Наличные",txt)

res={
    "price":price,
    "name":name,
    "total":total.group(1),
    "date":date.group(),
    "method":method.group()
}

print(json.dumps(res, indent=4, ensure_ascii=False))