import urllib.request
import json
import dml
import prov.model
import datetime
import uuid

def product(R, S):
    return [(t,u) for t in R for u in S]

def safety_zone(lat1, lon1, lat2, lon2):
    if (abs(lat1-lat2) < 1) and (abs(lon1-lon2) < 1):
        return True
    else:
        return False

class transformHubwayCrash(dml.Algorithm):
    contributor = 'nhuang54_wud'
    reads = ['nhuang54_wud.hubwayStation', 'nhuang54_wud.crashRecord']
    writes = ['nhuang54_wud.hubwayStationSafety']

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('nhuang54_wud', 'nhuang54_wud')

        # Get the data
        hubwayData = repo.nhuang54_wud.hubwayStation.find()
        crashData = repo.nhuang54_wud.crashRecord.find()

        # project hubway station locations in form (name, (lat, long))
        hubwayLocations = []
        for row in hubwayData:
            # print(row)
            # print(row['name'])
            # print(row['\ufeffX'])
            # print(row['Y'])
            hubwayLocations += [[row['name'], [float(row['\ufeffX']), float(row['Y'])]]]

        # project crash location in form (crash location id, (lat, long))
        crashLocations = []
        for row in crashData:
            if row['"mode_type"'] == 'bike':
                crashLocations += [[row['_id'], [float(row['"lat"']), float(row['"long"\r'])]]]

        #JOIN
        hubway_crash_prod = product(hubwayLocations, crashLocations)
        for t in hubway_crash_prod:
            print(t)
            print(t[0][0])
            print(t[0][1])
            print(t[0][1][0])
            print(t[0][1][1])
            print(t[1][0])
            print(t[1][1])
            break;
        hubway_safety_list = [(t[0][0], t[0][1], t[0][2], t[1][0], t[1][1], t[1][2], safety_zone(t[0][1], t[0][2], t[1][1], t[1][2])) for t in hubway_crash_prod]

        # put into dictionary
        hubway_safety_dict = {}
        for row in hubway_safety_list:
            hubway_safety_dict[row[0]] = {'latitude': row[1], 'longitude': row[2], 'safe zone': row[6]}

        # print(finalDict)
        print(hubway_safety_dict.items())

        with open("new_datasets/hubwaySafetyZone.json", 'w') as outfile:
          json.dump(hubway_safety_dict, outfile)

        repo.dropCollection("hubwayStationSafety")
        repo.createCollection("hubwayStationSafety")
        for key,value in hubway_safety_dict.items():
          repo['nhuang54_wud.hubwayStationSafety'].insert_one({key:value})
        # repo['nhuang54_wud.bikeCrashStreetlight'].insertMany()
        repo['nhuang54_wud.hubwayStationSafety'].metadata({'complete':True})
        print(repo['nhuang54_wud.hubwayStationSafety'].metadata())

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start":startTime, "end":endTime}

    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('nhuang54_wud', 'nhuang54_wud')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.

        this_script = doc.agent('alg:nhuang54_wud#transformHubwayCrash', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        resource1 = doc.entity('dat:nhuang54_wud#Hubway_Stations', {'prov:label':'311, Service Requests', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'csv'})
        resource2 = doc.entity('dat:nhuang54_wud#crash_open_data', {'prov:label':'311, Service Requests', prov.mode.PROV_TYPE:'ont:DataResource', 'ont:Extension':'csv'})

        transform_hubwayCrash = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(transform_hubwayCrash, this_script)

        doc.usage(transform_hubwayCrash, resource1, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Calculation',
                  'ont:Query':''
                  }
                  )
        doc.usage(transform_hubwayCrash, resource2, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Calculation',
                  'ont:Query':''
                  }
                  )

        hubwayStationSafety = doc.entity('dat:nhuang54_wud#hubwayStationSafety', {prov.model.PROV_LABEL:'Hubway location safety', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(hubwayStationSafety, this_script)
        doc.wasGeneratedBy(hubwayStationSafety, transform_hubwayCrash, endTime)
        doc.wasDerivedFrom(hubwayStationSafety, resource1, transform_hubwayCrash, transform_hubwayCrash, transform_hubwayCrash)
        doc.wasDerivedFrom(hubwayStationSafety, resource2, transform_hubwayCrash, transform_hubwayCrash, transform_hubwayCrash)


        repo.logout()

        return doc

'''
# This is example code you might use for debugging this module.
# Please remove all top-level function calls before submitting.
example.execute()
doc = example.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))
'''

if __name__ == '__main__':
    transformHubwayCrash.execute()

## eof
