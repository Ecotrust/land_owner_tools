import os
import sys
from django.core.management import setup_environ
thisdir = os.path.dirname(os.path.abspath(__file__))
appdir = os.path.realpath(os.path.join(thisdir, '..', 'lot'))
sys.path.append(appdir)
import settings
setup_environ(settings)
##############################
from trees.utils import angular_diff
import numpy as np
from scipy.spatial import KDTree
import math
import pandas as pd
from django.db import connection

def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def get_candidates(stand_list, min_candidates=5, tpa_factor=1.2):
    cursor = connection.cursor()

    dfs = []
    for sc in stand_list:

        class_clause = 'AND calc_dbh_class >= %d AND calc_dbh_class < %d' % (sc[1], sc[2]) 
        #class_clause = 'AND calc_dbh_class = %d' % (sc[1],) 

        sql = """
            SELECT 
                COND_ID, 
                SUM(SumOfTPA) as "TPA_%(species)s_%(lowsize)d_%(highsize)d",
                SUM(SumOfBA_FT2_AC) as "BAA_%(species)s_%(lowsize)d_%(highsize)d", 
                SUM(pct_of_totalba) as "PCTBA_%(species)s_%(lowsize)d_%(highsize)d",
                AVG(COUNT_SPECIESSIZECLASSES) as "PLOTCLASSCOUNT_%(species)s_%(lowsize)d_%(highsize)d", 
                AVG(TOTAL_BA_FT2_AC) as "PLOTBA_%(species)s_%(lowsize)d_%(highsize)d" 
            FROM treelive_summary 
            WHERE fia_forest_type_name = '%(species)s' 
            %(class_clause)s
            AND pct_of_totalba is not null
            GROUP BY COND_ID
        """ % { 'class_clause': class_clause, 
                'species': sc[0], 
                'lowsize': sc[1], 
                'highsize': sc[2]
                }

        cursor.execute(sql)
        rows = dictfetchall(cursor)

        if not rows:
            raise Exception("No matches for %s, %s-%s in" % (sc[0], sc[1], sc[2]))

        df = pd.DataFrame(rows)
        df.index = df['cond_id']
        del df['cond_id']
        dfs.append(df)

    if len(dfs) == 0:
        raise Exception("The stand list provided does not provide enough matches.")

    sdfs = sorted(dfs, key=lambda x: len(x), reverse=True)
    enough = False
    while not enough:
        candidates = pd.concat(sdfs, axis=1, join="inner")
        if len(candidates) < min_candidates:
            aa = sdfs.pop() # remove the one with smallest number
            print "Popping ", [x.replace("BAA_", "") for x in aa.columns.tolist() if x.startswith('BAA_')][0]
            continue
        else: 
            enough = True

        candidates['TOTAL_PCTBA'] = candidates[[x for x in candidates.columns if x.startswith('PCTBA')]].sum(axis=1)
        candidates['TOTAL_BA'] = candidates[[x for x in candidates.columns if x.startswith('BAA')]].sum(axis=1)
        candidates['TOTAL_TPA'] = candidates[[x for x in candidates.columns if x.startswith('TPA')]].sum(axis=1)
        candidates['PLOT_CLASS_COUNT'] = candidates[[x for x in candidates.columns if x.startswith('PLOTCLASSCOUNT')]].mean(axis=1)
        candidates['PLOT_BA'] = candidates[[x for x in candidates.columns if x.startswith('PLOTBA')]].mean(axis=1)
        candidates['SEARCH_CLASS_COUNT'] = len(stand_list)
        for x in candidates.columns:
            if x.startswith('PLOTCLASSCOUNT_') or x.startswith("PLOTBA_"):
                del candidates[x]

    return candidates

def get_sites(candidates):
    """ query for and return a dataframe of cond_id + site variables """
    cursor = connection.cursor()
    sql = """
        SELECT *
            -- COND_ID, calc_aspect, calc_slope
        FROM idb_summary 
        WHERE COND_ID IN (%s)
    """ % (",".join([str(x) for x in candidates.index.tolist()]))

    cursor.execute(sql)
    rows = dictfetchall(cursor)

    if rows:
        df = pd.DataFrame(rows)
        df.index = df['cond_id']
        del df['cond_id']
        return df
    else:
        raise Exception("No sites returned")

def get_nearest_neighbors(site_cond, stand_list, weight_dict=None, k=10):

    # process stand_list into dict
    tpa_dict = {}
    ba_dict = {}
    total_tpa = 0
    total_ba = 0
    for ssc in stand_list:
        key = '_'.join([str(x) for x in ssc[0:3]])
        total_tpa += ssc[3]
        tpa_dict[key] = ssc[3]
                
        ## est_ba = tpa * (0.005454 * dbh^2)
        est_ba = ssc[3] * (0.005454 * (((ssc[1] + ssc[2])/2)**2)) # assume middle of class
        total_ba += est_ba
        ba_dict[key] = est_ba

    # query for candidates 
    candidates = get_candidates(stand_list)

    # query for site variables and create dataframe
    sites = get_sites(candidates)

    # merge site data with candidates
    # candidates U site
    plotsummaries = pd.concat([candidates, sites], axis=1, join="inner")

    input_params = {}
    for attr in plotsummaries.axes[1].tolist():
        if attr.startswith("BAA_"): # or TPA?
            ssc = attr.replace("BAA_","")
            input_params[attr] = ba_dict[ssc] 
        elif attr == "TOTAL_PCTBA": 
            input_params[attr] = 100.0 #TODO don't assume 100%
        elif attr == "PLOT_BA":
            input_params[attr] = total_ba


    # Add site conditions
    input_params.update(site_cond)

    if not weight_dict:
        weight_dict = {}

    nearest = nearest_plots(input_params, plotsummaries, weight_dict, k)

    return nearest 

class NoPlotMatchError:
    pass

def nearest_plots(input_params, plotsummaries, weight_dict=None, k=10):
    if not weight_dict:
        weight_dict = {}

    search_params = input_params.copy()
    origkeys = search_params.keys()
    keys = [x for x in origkeys if x not in ['calc_aspect',]] # special case

    # assert that we have some candidates
    num_candidates = len(plotsummaries)
    if num_candidates == 0:
        raise NoPlotMatchError("There are no candidate plots matching the categorical variables: %s" % categories)

    ps_attr_list = []
    for cond_id in plotsummaries.index.tolist():
        ps = plotsummaries.ix[cond_id]

        vals = []
        for attr in keys:
            vals.append(ps[attr])

        # Aspect is a special case
        if 'calc_aspect' in origkeys:
            angle = angular_diff(ps['calc_aspect'], input_params['calc_aspect'])
            vals.append(angle)
            search_params['_aspect'] = 0 # anglular difference to self is 0
        
        ps_attr_list.append(vals)

    # include our special case
    if 'calc_aspect' in origkeys:
        keys.append('_aspect') 

    weights = np.ones(len(keys))
    for i in range(len(keys)):
        key = keys[i]
        if key in weight_dict:
            weights[i] = weight_dict[key]

    querypoint = np.array([float(search_params[attr]) for attr in keys])

    rawpoints = np.array(ps_attr_list) 

    # Normalize to max of 100; linear scale
    high = 100.0
    low = 0.0
    mins = np.min(rawpoints, axis=0)
    maxs = np.max(rawpoints, axis=0)
    rng = maxs - mins
    scaled_points = high - (((high - low) * (maxs - rawpoints)) / rng)
    scaled_querypoint = high - (((high - low) * (maxs - querypoint)) / rng)
    scaled_querypoint[np.isinf(scaled_querypoint)] = high  # replace all infinite values with high val

    # Apply weights
    # and guard against any nans due to zero range or other
    scaled_points = np.nan_to_num(scaled_points * weights) 
    scaled_querypoint = np.nan_to_num(scaled_querypoint * weights)

    # Create tree and query it for nearest plot
    tree = KDTree(scaled_points)
    querypoints = np.array([scaled_querypoint])
    result = tree.query(querypoints, k=k)
    distances = result[0][0]
    plots = result[1][0]

    top = zip(plots, distances)
    ps = []

    xs = [100 * x for x in weights if x > 0]
    squares = [x * x for x in xs]
    max_dist = math.sqrt(sum(squares)) # the real max 
    for t in top:
        if np.isinf(t[1]):
            continue
        try:
            pseries = plotsummaries.irow(t[0])
        except IndexError:
            continue

        # certainty of 0 -> distance is furthest possible
        # certainty of 1 -> the point matches exactly
        # sqrt of ratio taken to exagerate small diffs
        pseries = pseries.set_value('_kdtree_distance', t[1])
        pseries = pseries.set_value('_certainty', 1.0 - ((t[1] / max_dist) ** 0.5))

        ps.append(pseries)

    return ps, num_candidates

if __name__ == "__main__":

    stand_list = {
        'classes': [
            #('Douglas-fir', 6, 10, 160),
            #('Douglas-fir', 10, 14,  31),
            ('Douglas-fir', 6, 14, 191),
            ('Douglas-fir', 14, 18, 7),
            ('Western hemlock', 14, 18, 5),
            ('Western redcedar', 14, 18, 5),
            #('Red alder', 6, 20),
        ]
    }

    """
    stand_list = {
        'classes': [
            ('Douglas-fir', 10, 69),
            ('Western hemlock', 10, 20),
            ('Douglas-fir', 14, 5),
            ('Red alder', 10, 7),
            #('Tanoak', 2, 105),
            ('Western redcedar', 14, 2),
            #('Black cottonwood', 2, 67),
            ('Sitka spruce', 0, 60),
            ('Sitka spruce', 2, 3),
            #('Black cottonwood', 0, 97),
            #('Tanoak', 0, 200),
        ]
    }
    """

    site_cond = {
        "age_dom": 40,
        "calc_aspect": 360,
        "elev_ft": 1100,
        "latitude_fuzz": 45.58,
        "longitude_fuzz": -123.83,
        "calc_slope": 5
    }

    weight_dict = {
        'TOTAL_PCTBA': 5, 
        'PLOT_BA': 5,
        'age_dom': 5,
        "calc_aspect": 1,
        "elev_ft": 0.6,
        "latitude_fuzz": 0.3,
        "longitude_fuzz": 0.6,
        "calc_slope": 0.6,
    }

    ps, num_candidates = get_nearest_neighbors(site_cond, stand_list['classes'], weight_dict, k=5)

    print
    print "Candidates: ", num_candidates
    print
    print "\t".join(["cond", "certainty", "basal", "pct", "age"])
    for aa in ps:
        print "\t".join(str(x) for x in [aa.name , aa['_certainty'] * 100, aa['PLOT_BA'], aa['TOTAL_PCTBA'], aa['age_dom'] ])
    print
