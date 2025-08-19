import json, os

def readAndTranslateJsonActivityRefs(infile, outfile):
   with open(infile, "r") as file:
      data = json.load(file)

   #print (data)
   #print(data['activities'][1])

   #create named directory  of activities
   acts = {}
   for i in data['activities']:
       acts[i['identifier']]=i
      #print( i['identifier'])
      #print(len(i))


   for i in data['scoutgroups']:
      print( i['identifier'])
      for p in i['priorities']:
         print(p['activity'])
         p['activity'] = acts[p['activity']]

   with open(outfile, 'w') as f:
      json.dump(data, f)              
   
   


