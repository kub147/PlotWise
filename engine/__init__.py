"""PlotWise engine (workstream D): daily soil-water balance, yields, economics, scoring.

Modules:
    inputs        loaders for weather, crops, rotations, fields
    waterbalance  two-store daily soil-water balance (FAO-56 dual crop coefficient style)
    rotation      turns a rotation definition into a day-by-day crop schedule
    yields        K-State yield-vs-ET functions
    replay        runs every phase of every rotation through every year for one field
    scoring       indicators, criterion scores, weight-sensitivity analysis
    validate      comparison with the K-State Tribune trials
"""
