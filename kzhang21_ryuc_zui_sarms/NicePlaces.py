import dml
import pandas as pd
import prov.model
import requests
import zipfile
import random
import z3
import math
import logging
import datetime
from geopy.distance import geodesic

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class NicePlaces(dml.Algorithm):

    contributor = 'kzhang21_ryuc_zui_sarms'
    reads = ["kzhang21_ryuc_zui_sarms.yelp_business"]
    writes = ["kzhang21_ryuc_zui_sarms.nice_places"]

    @staticmethod
    def execute(trial=False):
        startTime = datetime.datetime.now()

        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('kzhang21_ryuc_zui_sarms', 'kzhang21_ryuc_zui_sarms')

        log.debug("Fetching data from kzhang21_ryuc_zui_sarms.yelp_business")
        
        data = list(repo["kzhang21_ryuc_zui_sarms.yelp_business"].find())
        
        
        # The coordinate 
        CURRENT_PLACE= (42.3601, -71.0589)
        
        # The number of places we pick 
        if trial:
            N = 5
        else:
            N = 500

        # What is the furthest you would like to go
        MAX_DIST = 100

        # What is the least amount of distance you would like to go
        MIN_DIST = 10

        # What is the average rating of the places you would like to go to
        AVG_RATE = 4
        # What is the average violation rating of the places you would like to go
        AVG_VIOR = 0

        Places = random.choices(data, k=N)    

        # Places: x_0 ... x_n are whether a place is chosen
        Xs = z3.Ints(" ".join(["x_%s" % i for i in range(N)]))
        
        # X can only 1 or 0
        X_const = [ 0<= xs for xs in Xs] + [xs <= 1 for xs in Xs]
        
        # Distances: d_0 ... d_n is the distance from the current place to the place_n
        Ds = z3.Reals(" ".join(["d_%s" % i for i in range(N)]))

        # Rating: r_0 ... r_n is the Yelp rating of the current place n
        Rs = z3.Reals(" ".join(["r_%s" % i for i in range(N)]))

        # Violations: v_0 ... v_n is the violation rating of the place
        Vs = z3.Reals(" ".join(["v_%s" % i for i in range(N)]))

        R_mapping = [(rs == ps["rating"]) for (rs, ps) in zip(Rs, Places)]

        V_mapping = [(vs == ps["violation_rate"]) for (vs, ps) in zip(Vs, Places)]

        # Fetch the coordinate pair from each of the place
        DPs = [(x["coordinates"]["latitude"], x["coordinates"]["longitude"]) for x in Places]
        Dists = [dist(CURRENT_PLACE, x) for x in DPs]
        log.debug("Dists %s", Dists)
        # Distance; d_0 ... d_n is the distance from the current place to the place n
        D_mapping = [(ds == dis) for (ds, dis) in zip(Ds, Dists)]

        D_const = [
            sum([xs * ds for (xs, ds) in zip(Xs, Ds)]) > MIN_DIST,
            sum([xs * ds for (xs, ds) in zip(Xs, Ds)]) <= MAX_DIST
            ]

        R_const = [
            (sum([xs*rs for (xs, rs) in zip(Xs, Rs)]) / N) >= AVG_RATE
        ]

        V_const = [
            (sum([xs*vs for (xs, vs) in zip(Xs, Vs)]) / N) <= AVG_RATE
        ]

        solver = z3.Solver()

        for c in X_const + R_mapping + V_mapping + D_mapping + D_const:
            log.debug("Adding constraint %s", c)
            solver.add(c)
        
        log.info("Solution is %s", solver.check())

        result = solver.model()

        print(" ".join([f"{result[x]}" for x in Xs]))
        for ix, x in enumerate(Xs):
            if result[x].as_long() != 0:
                print(f"We can go to |{Places[ix]['name']}| 👍")



        endTime = datetime.datetime.now()

        return {"start": startTime, "end": endTime}
    
    @staticmethod
    def provenance(doc=prov.model.ProvDocument(), startTime=None, endTime=None):
        return None

def dist(a, b):
    # lat_a, lgn_a = a
    
    # lat_b, lgn_b = b
    

    return geodesic(a, b).miles