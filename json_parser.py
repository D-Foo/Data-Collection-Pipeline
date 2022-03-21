import json
import string

#Convert a card set from mtgjson.com to a .txt containing the nanme of each individual card in the set

#Load json data
with open("NEO.json", 'r') as f:
    neo_data = json.load(f)
f.close()

#Get number of cards in json
set_size = neo_data["data"]["totalSetSize"]
name_list = []

#Get each name
for i in range(set_size):
    name_list.append(neo_data["data"]["cards"][i]["name"])

#Remove duplicates and sort
name_list =  set(name_list)
name_list = sorted(name_list)

#Write to txt
cardlist_txt = open('cardlist.txt', 'w')

for name in name_list:
    cardlist_txt.write(name + '\n')
cardlist_txt.close()