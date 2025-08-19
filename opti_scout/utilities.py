import json, os

def read_and_translate_json_activity_refs(infile, outfile):
   with open(infile, "r") as file:
      data = json.load(file)

   # Create named directory of activities
   acts = {}
   for i in data['activities']:
       acts[i['identifier']]=i

   for i in data['scoutgroups']:
      print( i['identifier'])
      for p in i['priorities']:
         print(p['activity'])
         p['activity'] = acts[p['activity']]

   with open(outfile, 'w') as f:
      json.dump(data, f)              
   
   


