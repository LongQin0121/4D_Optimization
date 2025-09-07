from pyBADA.bada4 import Bada4Aircraft, BADA4
from pyBADA.aircraft import Airplane
import pyBADA.atmosphere as atm
import math
import pandas as pd
import numpy as np
import pyBADA.conversions as conv


def initialize_aircraft_model(ac_model):
    """Initialize aircraft model and BADA4 object"""
    bada_version = "4.2"
    filepath = "/home/longqin/Downloads/4.2/BADA_4.2_L06514UPC/Models"
    
    AC = Bada4Aircraft(
        badaVersion=bada_version,
        acName=ac_model,
        filePath=filepath,
    )
    
    bada4 = BADA4(AC)
    return bada4


def determine_speed_profile(flight_level, crossover_fl, descent_mach, high_cas, 
                           low_cas, low_cas_fl, constant_cas):
    """Determine speed profile parameters for a given flight level"""
    if constant_cas is None and flight_level >= crossover_fl:
        # Use specified Mach number
        M = descent_mach
        speed_mode = f"Mach {descent_mach}"
        flight_evolution = "constM"
        target_cas = None
    elif low_cas_fl is not None and flight_level >= low_cas_fl:
        # Use high altitude CAS
        M = None  # Will be calculated later
        speed_mode = f"CAS {high_cas}kt"
        flight_evolution = "constCAS"
        target_cas = high_cas
    elif low_cas_fl is not None and low_cas is not None:
        # Use low altitude CAS
        M = None  # Will be calculated later
        speed_mode = f"CAS {low_cas}kt"
        flight_evolution = "constCAS"
        target_cas = low_cas
    else:
        # No intermediate CAS, use high altitude CAS
        M = None  # Will be calculated later
        speed_mode = f"CAS {high_cas}kt"
        flight_evolution = "constCAS"
        target_cas = high_cas
    
    return M, speed_mode, flight_evolution, target_cas


def calculate_performance_at_altitude(flight_level, aircraft_mass, bada4, 
                                    crossover_fl, descent_mach, high_cas, 
                                    low_cas, low_cas_fl, constant_cas, DeltaTemp=0,
                                    force_cas=None):
    """Calculate descent performance at specified flight level, with option to force CAS"""
    altitude_ft = flight_level * 100
    altitude_m = conv.ft2m(altitude_ft)
    
    # Calculate atmospheric properties
    theta_val, delta_val, sigma_val = atm.atmosphereProperties(altitude_m, DeltaTemp)
    
    # Determine speed profile parameters
    if force_cas is None:
        M, speed_mode, flight_evolution, target_cas = determine_speed_profile(
            flight_level, crossover_fl, descent_mach, high_cas, 
            low_cas, low_cas_fl, constant_cas
        )
    else:
        # Force a specific CAS value
        M = None
        speed_mode = f"CAS {force_cas}kt"
        flight_evolution = "constCAS"
        target_cas = force_cas
    
    # Calculate actual Mach number, CAS, TAS
    if M is not None:
        # Mach number known, calculate CAS and TAS
        tas = atm.mach2Tas(M, theta_val)
        cas = atm.mach2Cas(M, theta_val, delta_val, sigma_val)
    else:
        # CAS known, calculate Mach and TAS
        cas = conv.kt2ms(target_cas)
        tas = atm.cas2Tas(cas, delta_val, sigma_val)
        M = atm.tas2Mach(tas, theta_val)
    
    # Dynamically calculate Energy Share Factor
    esf_des = Airplane.esf(
        h=altitude_m,
        DeltaTemp=DeltaTemp,
        flightEvolution=flight_evolution,
        phase="des",
        M=M
    )
    
    # Calculate lift coefficient
    cl = bada4.CL(delta=delta_val, mass=aircraft_mass, M=M)
    
    # Calculate drag coefficient (clean configuration)
    HLid = 0.0  # No flaps
    LG = "LGUP"  # Landing gear up
    cd = bada4.CD(HLid=HLid, LG=LG, CL=cl, M=M)
    
    # Calculate drag
    drag = bada4.D(delta=delta_val, M=M, CD=cd)
    
    # Calculate idle thrust
    idle_thrust = bada4.Thrust(
        delta=delta_val,
        theta=theta_val,
        M=M,
        rating="LIDL",  # Idle setting
        DeltaTemp=DeltaTemp
    )
    
    # Calculate fuel flow (kg/s)
    fuel_flow = bada4.ff(
        delta=delta_val,
        theta=theta_val,
        M=M,
        rating="LIDL",  # Idle setting
        DeltaTemp=DeltaTemp
    )
    
    # Calculate idle descent rate
    idle_descent_rate = bada4.ROCD(
        T=idle_thrust,
        D=drag,
        v=tas,
        mass=aircraft_mass,
        ESF=esf_des,
        h=altitude_m,
        DeltaTemp=DeltaTemp
    )
    
    # Calculate descent angle (degrees)
    if tas > 0:
        descent_angle = math.degrees(math.asin(idle_descent_rate / tas))
    else:
        descent_angle = 0
    
    # Calculate descent gradient (percentage)
    descent_gradient = 100 * abs(idle_descent_rate / tas) if tas > 0 else 0
    
    # Calculate altitude-distance ratio
    ft_per_nm = abs(idle_descent_rate * 196.85 / conv.ms2kt(tas) * 60) if conv.ms2kt(tas) > 0 else 0
    
    return {
        "FL": flight_level,
        "Altitude(ft)": altitude_ft,
        "Speed Mode": speed_mode,
        "Mach": round(M, 3),
        "CAS(kt)": round(conv.ms2kt(cas), 1),
        "TAS(kt)": round(conv.ms2kt(tas), 1),
        "Descent Rate(ft/min)": round(idle_descent_rate * 196.85, 0),
        "Descent Rate(m/s)": round(idle_descent_rate, 2),
        "Descent Angle(deg)": round(descent_angle, 2),
        "Descent Gradient(%)": round(descent_gradient, 2),
        "Alt-Dist Ratio(ft/nm)": round(ft_per_nm, 0),
        "ESF": round(esf_des, 3),
        "Drag(N)": round(drag, 0),
        "Idle Thrust(N)": round(idle_thrust, 0),
        "Fuel Flow(kg/h)": round(fuel_flow * 3600, 1),
        "Fuel Flow(kg/s)": round(fuel_flow, 4),
        "Lift Coefficient": round(cl, 3),
        "Drag Coefficient": round(cd, 4),
        "Is Deceleration Point": False
    }


def generate_flight_levels(cruise_fl, target_fl):
    """Generate a list of flight levels during descent"""
    flight_levels = []
    for fl in range(cruise_fl, target_fl-1, -10):
        flight_levels.append(fl)
    if target_fl not in flight_levels:
        flight_levels.append(target_fl)
    return flight_levels


def create_speed_profile_name(constant_cas, high_cas, low_cas, low_cas_fl, descent_mach):
    """Create speed profile name"""
    if constant_cas is not None:
        if high_cas == low_cas:
            return f"{high_cas}kt constant"
        else:
            return f"{high_cas}kt→{low_cas}kt@FL{low_cas_fl}"
    else:
        if high_cas == low_cas:
            return f"{descent_mach}M/{high_cas}kt"
        else:
            return f"{descent_mach}M/{high_cas}kt/{low_cas}kt@FL{low_cas_fl}"


def calculate_deceleration_segment(current_cas, target_cas, fuel_flow_kg_per_sec):
    """
    Calculate distance, time and fuel for a single deceleration segment
    
    Parameters:
    current_cas: Current CAS (kt)
    target_cas: Target CAS (kt) 
    fuel_flow_kg_per_sec: Fuel flow (kg/s)
    
    Returns:
    (deceleration distance(nm), deceleration time(s), deceleration fuel(kg))
    """
    if current_cas <= target_cas:
        return 0, 0, 0
    
    # According to requirements: time is 1 second per knot, distance is 0.1 nm per knot
    decel_distance_nm = (current_cas - target_cas) / 10
    decel_time_sec = (current_cas - target_cas)  # 1 second per knot
    decel_fuel = fuel_flow_kg_per_sec * decel_time_sec
    
    return decel_distance_nm, decel_time_sec, decel_fuel


def calculate_detailed_descent_with_deceleration(cruise_fl, target_fl, aircraft_mass, 
                                              descent_mach, high_cas, ac_model,
                                              low_cas=None, low_cas_fl=100,
                                              constant_cas=None):
    """
    Calculate detailed descent profile including deceleration segments as level flight
    """
    # Initialize aircraft model
    bada4 = initialize_aircraft_model(ac_model)
    
    # Set low altitude CAS
    if low_cas is None:
        low_cas = high_cas
    
    # Set parameters for constant CAS descent
    if constant_cas is not None:
        descent_mach = 0.9  # Set a higher Mach number to ensure crossover altitude is above cruise altitude
        high_cas = constant_cas
        low_cas = constant_cas
    
    # Calculate crossover altitude
    high_cas_ms = conv.kt2ms(high_cas)
    crossover_m = atm.crossOver(cas=high_cas_ms, Mach=descent_mach)
    crossover_ft = conv.m2ft(crossover_m)
    crossover_fl = int(crossover_ft / 100)
    
    # Create speed profile name
    profile_name = create_speed_profile_name(constant_cas, high_cas, low_cas, low_cas_fl, descent_mach)
    
    # Generate flight levels list
    flight_levels = generate_flight_levels(cruise_fl, target_fl)
    
    # Create a list to store the deceleration segments
    decel_segments = []
    
    # Create a list to store all data points (including deceleration points)
    result_points = []
    
    # Current accumulated values
    cum_distance = 0.0
    cum_time = 0.0
    cum_fuel = 0.0
    
    # Keep track of the current CAS limit at each level
    current_cas_limit = None
    
    # Process each flight level
    for i, fl in enumerate(flight_levels):
        # Determine if this is a deceleration point
        is_fl100 = (fl == 100)
        is_low_cas_fl = (fl == low_cas_fl) if low_cas_fl is not None else False
        is_fl30 = (fl == 30)
        
        # Calculate performance at this flight level (using normal speed schedule)
        point_data = calculate_performance_at_altitude(
            fl, aircraft_mass, bada4, crossover_fl, descent_mach, 
            high_cas, low_cas, low_cas_fl, constant_cas,
            force_cas=current_cas_limit
        )
        
        # Add accumulated data
        if i > 0:
            # Calculate distance, time, and fuel for descent from previous level
            prev_point = result_points[-1]
            altitude_diff = (prev_point['FL'] - fl) * 100  # In feet
            
            # Use average of previous and current point for calculations
            avg_alt_dist_ratio = (prev_point['Alt-Dist Ratio(ft/nm)'] + point_data['Alt-Dist Ratio(ft/nm)']) / 2
            if avg_alt_dist_ratio > 0:
                segment_distance = altitude_diff / avg_alt_dist_ratio
            else:
                segment_distance = 0
                
            avg_tas_kt = (prev_point['TAS(kt)'] + point_data['TAS(kt)']) / 2
            avg_tas_nm_per_sec = avg_tas_kt / 3600  # Convert to nm/s
            
            if avg_tas_nm_per_sec > 0:
                segment_time = segment_distance / avg_tas_nm_per_sec
            else:
                segment_time = 0
                
            avg_fuel_flow = (prev_point['Fuel Flow(kg/s)'] + point_data['Fuel Flow(kg/s)']) / 2
            segment_fuel = avg_fuel_flow * segment_time
            
            # Update accumulated values
            cum_distance += segment_distance
            cum_time += segment_time
            cum_fuel += segment_fuel
        
        # Add accumulated values to the point data
        point_data['Cumulative Distance(nm)'] = round(cum_distance, 1)
        point_data['Cumulative Time(s)'] = round(cum_time, 0)
        point_data['Cumulative Fuel(kg)'] = round(cum_fuel, 1)
        
        # Add this point to the results
        result_points.append(point_data)
        
        # Check if we need to add deceleration segments at this flight level
        need_deceleration = False
        target_cas = None
        decel_type = None
        
        # FL100 - Statutory speed limit (250kt)
        if is_fl100 and point_data['CAS(kt)'] > 250:
            need_deceleration = True
            target_cas = 250
            decel_type = "Statutory Deceleration"
            current_cas_limit = 250
            
        # User defined low_cas_fl - Profile deceleration
        elif is_low_cas_fl and low_cas is not None and point_data['CAS(kt)'] > low_cas:
            need_deceleration = True
            target_cas = low_cas
            decel_type = "Profile Deceleration"
            current_cas_limit = low_cas
            
        # FL30 - Approach speed limit (220kt)
        elif is_fl30 and point_data['CAS(kt)'] > 220:
            need_deceleration = True
            target_cas = 220
            decel_type = "Approach Deceleration"
            current_cas_limit = 220
        
        # Add deceleration segment if needed
        if need_deceleration:
            current_cas = point_data['CAS(kt)']
            
            # Calculate deceleration parameters
            decel_dist, decel_time, decel_fuel = calculate_deceleration_segment(
                current_cas, target_cas, point_data['Fuel Flow(kg/s)']
            )
            
            # Record this deceleration segment
            decel_segment = {
                'type': decel_type,
                'FL': fl,
                'CAS before': current_cas,
                'CAS after': target_cas,
                'Distance(nm)': decel_dist,
                'Time(s)': decel_time,
                'Fuel(kg)': decel_fuel,
                'TAS(kt)': point_data['TAS(kt)']
            }
            decel_segments.append(decel_segment)
            
            # Create a new data point after deceleration (same FL, new CAS)
            decel_point = calculate_performance_at_altitude(
                fl, aircraft_mass, bada4, crossover_fl, descent_mach, 
                high_cas, low_cas, low_cas_fl, constant_cas,
                force_cas=target_cas
            )
            
            # Mark as a deceleration point
            decel_point['Is Deceleration Point'] = True
            
            # Update accumulated values
            cum_distance += decel_dist
            cum_time += decel_time
            cum_fuel += decel_fuel
            
            # Add accumulated values to the deceleration point
            decel_point['Cumulative Distance(nm)'] = round(cum_distance, 1)
            decel_point['Cumulative Time(s)'] = round(cum_time, 0)
            decel_point['Cumulative Fuel(kg)'] = round(cum_fuel, 1)
            
            # Add this point to the results
            result_points.append(decel_point)
    
    # Create DataFrame from all points
    df = pd.DataFrame(result_points)
    
    # Calculate summary information
    total_distance = df.iloc[-1]['Cumulative Distance(nm)']
    total_time = df.iloc[-1]['Cumulative Time(s)']
    total_fuel = df.iloc[-1]['Cumulative Fuel(kg)']
    total_altitude_change = (cruise_fl - target_fl) * 100
    avg_ft_per_nm = total_altitude_change / total_distance if total_distance > 0 else 0
    
    summary = {
        "Profile": profile_name,
        "Descent Distance (nm)": round(total_distance, 1),
        "Descent Time (s)": round(total_time, 0),
        "Fuel Consumption (kg)": round(total_fuel, 1),
        "Average Fuel Flow (kg/h)": round(total_fuel/(total_time/3600), 1) if total_time > 0 else 0,
        "Average Descent Gradient (%)": round(total_altitude_change/6076.12/total_distance*100, 2) if total_distance > 0 else 0,
        "Altitude-to-Distance Ratio (ft/nm)": round(avg_ft_per_nm, 1)
    }
    
    return summary, df, decel_segments


def print_deceleration_segments_table(decel_segments):
    """Print deceleration segments analysis table"""
    if decel_segments:
        print("\nDeceleration Segments Analysis:")
        print("-" * 120)
        print(f"{'Type':<12}{'Flight Level':<10}{'CAS before':<12}{'CAS after':<12}{'Distance(nm)':<12}{'Time(s)':<10}{'Fuel(kg)':<12}{'TAS(kt)':<10}")
        print("-" * 120)
        
        for segment in decel_segments:
            print(f"{segment['type']:<12}FL{segment['FL']:<8}{segment['CAS before']:<12.1f}"
                  f"{segment['CAS after']:<12.1f}{segment['Distance(nm)']:<12.1f}"
                  f"{segment['Time(s)']:<10.0f}{segment['Fuel(kg)']:<12.1f}{segment['TAS(kt)']:<10.1f}")
        
        print("-" * 120)


def print_final_profile_table(df):
    """Print final descent profile table with deceleration segments"""
    print("\nDetailed Descent Data after Adding Deceleration Segments:")
    print("-" * 180)
    
    # Select key columns to display
    display_columns = [
        'FL', 'Speed Mode', 'Mach', 'CAS(kt)', 'TAS(kt)', 
        'Descent Rate(ft/min)', 'Descent Gradient(%)', 'Alt-Dist Ratio(ft/nm)',
        'Fuel Flow(kg/h)', 'Cumulative Distance(nm)', 'Cumulative Time(s)', 'Cumulative Time(min)', 'Cumulative Fuel(kg)'
    ]
    
    # Calculate minutes column for display
    df_display = df.copy()
    df_display['Cumulative Time(min)'] = df['Cumulative Time(s)'] / 60
    
    # Print header
    header = ""
    for col in display_columns:
        if col in ['FL', 'Mach', 'CAS(kt)', 'TAS(kt)']:
            header += f"{col:>8}"
        elif col in ['Speed Mode']:
            header += f"{col:>12}"
        elif col in ['Descent Rate(ft/min)', 'Descent Gradient(%)', 'Alt-Dist Ratio(ft/nm)', 'Fuel Flow(kg/h)']:
            header += f"{col:>12}"
        elif col in ['Cumulative Time(s)']:
            header += f"{col:>12}"
        elif col in ['Cumulative Time(min)']:
            header += f"{col:>12}"
        else:
            header += f"{col:>14}"
    print(header)
    print("-" * 180)
    
    # Print data rows
    for _, row in df_display.iterrows():
        # Check if this is a deceleration point
        is_decel = row.get('Is Deceleration Point', False)
        
        line = ""
        for col in display_columns:
            value = row[col]
            if col in ['FL']:
                line += f"{value:>8.0f}"
            elif col in ['Mach']:
                line += f"{value:>8.3f}"
            elif col in ['CAS(kt)', 'TAS(kt)']:
                line += f"{value:>8.1f}"
            elif col in ['Speed Mode']:
                line += f"{str(value):>12}"
            elif col in ['Descent Rate(ft/min)', 'Alt-Dist Ratio(ft/nm)', 'Cumulative Time(s)']:
                line += f"{value:>12.0f}"
            elif col in ['Cumulative Time(min)']:
                line += f"{value:>12.1f}"
            elif col in ['Descent Gradient(%)']:
                line += f"{value:>12.2f}"
            elif col in ['Fuel Flow(kg/h)']:
                line += f"{value:>12.1f}"
            else:
                line += f"{value:>14.1f}"
                
        # Mark deceleration points with asterisk
        if is_decel:
            line += " *"
            
        print(line)
    
    print("-" * 180)
    print("* Indicates point after deceleration")


def print_summary(summary):
    """Print descent profile summary"""
    print(f"\nDescent Profile Summary:")
    print(f"Total Descent Distance: {summary['Descent Distance (nm)']} nm")
    print(f"Total Descent Time: {summary['Descent Time (s)']} seconds ({summary['Descent Time (s)']/60:.1f} minutes)")
    print(f"Total Fuel Consumption: {summary['Fuel Consumption (kg)']} kg")
    print(f"Average Fuel Flow: {summary['Average Fuel Flow (kg/h)']} kg/h")
    print(f"Average Descent Gradient: {summary['Average Descent Gradient (%)']} %")
    print(f"Altitude-Distance Ratio: {summary['Altitude-to-Distance Ratio (ft/nm)']} ft/nm")
    print("=" * 80)


def calculate_descent_profile(cruise_fl, target_fl, aircraft_mass, ac_model, 
                            descent_mach, high_cas, 
                            intermediate_cas=None, intermediate_fl=None,
                            final_approach_cas=220, final_approach_fl=30,
                            print_details=True):
    """
    Unified descent profile calculation function - optimized parameter call
    
    Parameters:
    cruise_fl: int - Cruise flight level
    target_fl: int - Target flight level
    aircraft_mass: float - Aircraft mass (kg)
    ac_model: str - Aircraft model
    descent_mach: float - Descent Mach number
    high_cas: int - High-altitude calibrated airspeed (kt)
    intermediate_cas: int or None - Intermediate deceleration target speed (kt), None means not used
    intermediate_fl: int or None - Intermediate deceleration flight level, None means not used
    final_approach_cas: int - Final approach speed (kt), default 220 kt
    final_approach_fl: int - Final approach deceleration flight level, default FL30
    print_details: bool - Whether to print detailed information
    
    Returns:
    tuple: (summary, df, decel_segments)
    """
    # Set low altitude CAS and FL
    low_cas = intermediate_cas
    low_cas_fl = intermediate_fl
    
    # Calculate the detailed descent profile with deceleration segments
    summary, df, decel_segments = calculate_detailed_descent_with_deceleration(
        cruise_fl=cruise_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        descent_mach=descent_mach,
        high_cas=high_cas,
        ac_model=ac_model,
        low_cas=low_cas,
        low_cas_fl=low_cas_fl
    )
    
    if print_details:
        # Print header information
        print(f"\n{'='*80}")
        print(f"Descent Profile Analysis: {ac_model}")
        print(f"{'='*80}")
        print(f"Aircraft Weight: {aircraft_mass/1000:.1f} tonnes")
        print(f"Descent Profile: {summary['Profile']}")
        print(f"Cruise Altitude: FL{cruise_fl} ({cruise_fl*100:,} ft)")
        print(f"Target Altitude: FL{target_fl} ({target_fl*100:,} ft)")
        print(f"{'='*80}")
        
        # Print deceleration segments
        print_deceleration_segments_table(decel_segments)
        
        # Print detailed profile
        print_final_profile_table(df)
        
        # Print summary
        print_summary(summary)
    
    return summary, df, decel_segments


# ======================== Example ========================

# Example: 0.73M/270kt，220kt@FL50
# summary, df, decel_segments = calculate_descent_profile(
#     cruise_fl=370,
#     target_fl=30,
#     aircraft_mass=60000,
#     ac_model="A320-232",
#     descent_mach=0.73,
#     high_cas=270,
#     intermediate_cas=220, 
#     intermediate_fl=50,
#     print_details=True
# )