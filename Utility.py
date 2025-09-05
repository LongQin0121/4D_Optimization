from pyBADA.bada4 import Bada4Aircraft, BADA4
import pyBADA.atmosphere as atm
import pyBADA.conversions as conv

def mach2tas_kt(flight_level, mach, delta_temp=0):
    """
    Simple function to calculate True Airspeed (TAS) from flight level and Mach number
    
    Parameters:
    flight_level: Flight level (FL)
    mach: Mach number
    delta_temp: Temperature deviation from ISA, default is 0
    
    Returns:
    float: True airspeed (TAS) in knots
    """

    # Calculate altitude in meters
    altitude_ft = flight_level * 100
    altitude_m = conv.ft2m(altitude_ft)
    
    # Calculate atmospheric properties
    theta_val, delta_val, sigma_val = atm.atmosphereProperties(altitude_m, delta_temp)
    
    # Calculate true airspeed (TAS)
    tas_ms = atm.mach2Tas(mach, theta_val)
    tas_kt = conv.ms2kt(tas_ms)
    
    return tas_kt