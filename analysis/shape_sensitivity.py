"""Hypothetical error distributions with the SAME central 95% half-width.

These t distributions are counterexamples to identifying extreme tails from
a 95% interval alone; they are not fitted models for the Ipsos survey.
"""
from scipy.stats import t


def scenarios(error_pp=8.43, margin_pp=2.1):
    result=[]
    for df in [5,10,30]:
        scale=margin_pp/t.ppf(.975,df)
        result.append({"df":df,"scale_pp":float(scale),
                       "p":float(2*t.sf(abs(error_pp)/scale,df))})
    return result
