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
    elif flight_level >= low_cas_fl:
        # Use high altitude CAS
        M = None  # Will be calculated later
        speed_mode = f"CAS {high_cas}kt"
        flight_evolution = "constCAS"
        target_cas = high_cas
    else:
        # Use low altitude CAS
        M = None  # Will be calculated later
        speed_mode = f"CAS {low_cas}kt"
        flight_evolution = "constCAS"
        target_cas = low_cas
    
    return M, speed_mode, flight_evolution, target_cas

def calculate_performance_at_altitude(flight_level, aircraft_mass, bada4, 
                                    crossover_fl, descent_mach, high_cas, 
                                    low_cas, low_cas_fl, constant_cas, DeltaTemp=0):
    """Calculate descent performance at specified flight level"""
    altitude_ft = flight_level * 100
    altitude_m = conv.ft2m(altitude_ft)
    
    # Calculate atmospheric properties
    theta_val, delta_val, sigma_val = atm.atmosphereProperties(altitude_m, DeltaTemp)
    
    # Determine speed profile parameters
    M, speed_mode, flight_evolution, target_cas = determine_speed_profile(
        flight_level, crossover_fl, descent_mach, high_cas, 
        low_cas, low_cas_fl, constant_cas
    )
    
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
        "Drag Coefficient": round(cd, 4)
    }

def generate_flight_levels(cruise_fl, target_fl):
    """Generate a list of flight levels during descent"""
    flight_levels = []
    for fl in range(cruise_fl, target_fl-1, -10):
        flight_levels.append(fl)
    if target_fl not in flight_levels:
        flight_levels.append(target_fl)
    return flight_levels

def calculate_cumulative_data(df, flight_levels):
    """Calculate cumulative distance, time, and fuel consumption"""
    horizontal_distance = np.zeros(len(flight_levels))
    fuel_consumption = np.zeros(len(flight_levels))
    time_elapsed = np.zeros(len(flight_levels))
    
    for i in range(1, len(flight_levels)):
        # Calculate altitude difference between adjacent flight levels (feet)
        altitude_diff = (flight_levels[i-1] - flight_levels[i]) * 100
        # Use average alt-dist ratio of the two points
        avg_ft_per_nm = (df.iloc[i-1]['Alt-Dist Ratio(ft/nm)'] + df.iloc[i]['Alt-Dist Ratio(ft/nm)']) / 2
        if avg_ft_per_nm > 0:
            segment_distance = altitude_diff / avg_ft_per_nm
        else:
            segment_distance = 0
        # Cumulative horizontal distance
        horizontal_distance[i] = horizontal_distance[i-1] + segment_distance
        
        # Calculate time and fuel
        avg_tas_kt = (df.iloc[i-1]['TAS(kt)'] + df.iloc[i]['TAS(kt)']) / 2
        avg_tas_nm_per_sec = avg_tas_kt / 3600  # Convert to nm/s
        if avg_tas_nm_per_sec > 0:
            segment_time_seconds = segment_distance / avg_tas_nm_per_sec
        else:
            segment_time_seconds = 0
        
        time_elapsed[i] = time_elapsed[i-1] + segment_time_seconds
        
        avg_fuel_flow = (df.iloc[i-1]['Fuel Flow(kg/s)'] + df.iloc[i]['Fuel Flow(kg/s)']) / 2
        segment_fuel = avg_fuel_flow * segment_time_seconds
        fuel_consumption[i] = fuel_consumption[i-1] + segment_fuel
    
    return horizontal_distance, time_elapsed, fuel_consumption

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

def calculate_basic_descent_profile(cruise_fl, target_fl, aircraft_mass, 
                                  descent_mach, high_cas, ac_model, 
                                  low_cas=None, low_cas_fl=100, 
                                  constant_cas=None, print_details=True):
    """
    Calculate basic descent profile (without deceleration segments)
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
        low_cas = constant_cas if low_cas is None else low_cas
    
    # Calculate crossover altitude
    high_cas_ms = conv.kt2ms(high_cas)
    crossover_m = atm.crossOver(cas=high_cas_ms, Mach=descent_mach)
    crossover_ft = conv.m2ft(crossover_m)
    crossover_fl = int(crossover_ft / 100)
    
    # Create speed profile name
    profile_name = create_speed_profile_name(constant_cas, high_cas, low_cas, low_cas_fl, descent_mach)
    
    if print_details:
        print(f"\n{'='*80}")
        print(f"Basic Descent Profile Analysis: {ac_model}")
        print(f"{'='*80}")
        print(f"Aircraft Weight: {aircraft_mass/1000:.1f} tonnes")
        print(f"Descent Profile: {profile_name}")
        print(f"Cruise Altitude: FL{cruise_fl} ({cruise_fl*100:,} ft)")
        print(f"Target Altitude: FL{target_fl} ({target_fl*100:,} ft)")
        print(f"Crossover Altitude: FL{crossover_fl} ({crossover_fl*100:,} ft)")
        print(f"{'='*80}")
    
    # Generate flight levels list
    flight_levels = generate_flight_levels(cruise_fl, target_fl)
    
    # Calculate performance at each flight level
    results = []
    for fl in flight_levels:
        result = calculate_performance_at_altitude(
            fl, aircraft_mass, bada4, crossover_fl, descent_mach, 
            high_cas, low_cas, low_cas_fl, constant_cas
        )
        results.append(result)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Calculate cumulative data
    horizontal_distance, time_elapsed, fuel_consumption = calculate_cumulative_data(df, flight_levels)
    
    # Add cumulative data to DataFrame
    df['Cumulative Distance(nm)'] = [round(d, 1) for d in horizontal_distance]
    df['Cumulative Time(s)'] = [round(t, 0) for t in time_elapsed]
    df['Cumulative Fuel(kg)'] = [round(f, 1) for f in fuel_consumption]
    
    if print_details:
        print_basic_profile_table(df, profile_name)
    
    # Calculate summary information
    total_distance = horizontal_distance[-1]
    total_time = time_elapsed[-1]
    total_fuel = fuel_consumption[-1]
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
    
    if print_details:
        print_summary(summary)
    
    return summary, df, flight_levels

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

def find_altitude_index(flight_levels, target_fl):
    """Find index near target flight level"""
    for i in range(1, len(flight_levels)):
        if flight_levels[i-1] > target_fl >= flight_levels[i]:
            return i
    return None

def apply_fl100_deceleration(decel_segments, new_df, flight_levels, 
                           horizontal_distance, time_elapsed, fuel_consumption):
    """Apply FL100 statutory speed limit deceleration segment"""
    fl100_index = find_altitude_index(flight_levels, 100)
    
    if fl100_index is not None:
        current_cas = new_df.iloc[fl100_index-1]['CAS(kt)']
        
        if current_cas > 250:
            fuel_flow = new_df.iloc[fl100_index-1]['Fuel Flow(kg/s)']
            
            decel_dist, decel_time, decel_fuel = calculate_deceleration_segment(
                current_cas, 250, fuel_flow
            )
            
            decel_segments.append({
                'type': 'Statutory Deceleration',
                'FL': 100,
                'CAS before': current_cas,
                'CAS after': 250,
                'Distance(nm)': decel_dist,
                'Time(s)': decel_time,
                'Fuel(kg)': decel_fuel,
                'TAS(kt)': new_df.iloc[fl100_index-1]['TAS(kt)']
            })
            
            # 修复：正确更新FL100及以下所有高度的CAS值
            for i in range(fl100_index, len(new_df)):  # 注意这里改为fl100_index而不是fl100_index-1
                if new_df.iloc[i]['CAS(kt)'] > 250:
                    new_df.at[new_df.index[i], 'CAS(kt)'] = 250.0  # 使用正确的索引
                    # 同时更新Speed Mode显示
                    new_df.at[new_df.index[i], 'Speed Mode'] = 'CAS 250kt'
            
            # Add deceleration segment's distance, time and fuel to all points after FL100
            horizontal_distance[fl100_index:] += decel_dist
            time_elapsed[fl100_index:] += decel_time
            fuel_consumption[fl100_index:] += decel_fuel
    
    return fl100_index

def apply_profile_deceleration(decel_segments, new_df, flight_levels, high_cas, low_cas, 
                             low_cas_fl, fl100_index, horizontal_distance, time_elapsed, fuel_consumption):
    """Apply profile deceleration segment"""
    if low_cas is not None and low_cas_fl is not None and low_cas != high_cas and low_cas > 0:
        low_cas_index = find_altitude_index(flight_levels, low_cas_fl)
        
        # Avoid duplicate calculation of FL100 deceleration
        if low_cas_index is not None and (low_cas_fl != 100 or fl100_index is None):
            current_cas = new_df.iloc[low_cas_index-1]['CAS(kt)']
            
            if current_cas > low_cas:
                fuel_flow = new_df.iloc[low_cas_index-1]['Fuel Flow(kg/s)']
                
                decel_dist, decel_time, decel_fuel = calculate_deceleration_segment(
                    current_cas, low_cas, fuel_flow
                )
                
                decel_segments.append({
                    'type': 'Profile Deceleration',
                    'FL': low_cas_fl,
                    'CAS before': current_cas,
                    'CAS after': low_cas,
                    'Distance(nm)': decel_dist,
                    'Time(s)': decel_time,
                    'Fuel(kg)': decel_fuel,
                    'TAS(kt)': new_df.iloc[low_cas_index-1]['TAS(kt)']
                })
                
                # 修复：正确更新指定FL及以下所有高度的CAS值
                for i in range(low_cas_index, len(new_df)):
                    if new_df.iloc[i]['CAS(kt)'] > low_cas:
                        new_df.at[new_df.index[i], 'CAS(kt)'] = float(low_cas)
                        # 同时更新Speed Mode显示
                        new_df.at[new_df.index[i], 'Speed Mode'] = f'CAS {low_cas}kt'
                
                horizontal_distance[low_cas_index:] += decel_dist
                time_elapsed[low_cas_index:] += decel_time
                fuel_consumption[low_cas_index:] += decel_fuel

def apply_approach_deceleration(decel_segments, new_df, flight_levels, 
                              horizontal_distance, time_elapsed, fuel_consumption):
    """Apply FL30 final approach deceleration segment"""
    fl030_index = find_altitude_index(flight_levels, 30)
    
    if fl030_index is not None:
        current_cas = new_df.iloc[fl030_index-1]['CAS(kt)']
        
        if current_cas > 220:
            fuel_flow = new_df.iloc[fl030_index-1]['Fuel Flow(kg/s)']
            
            decel_dist, decel_time, decel_fuel = calculate_deceleration_segment(
                current_cas, 220, fuel_flow
            )
            
            decel_segments.append({
                'type': 'Approach Deceleration',
                'FL': 30,
                'CAS before': current_cas,
                'CAS after': 220,
                'Distance(nm)': decel_dist,
                'Time(s)': decel_time,
                'Fuel(kg)': decel_fuel,
                'TAS(kt)': new_df.iloc[fl030_index-1]['TAS(kt)']
            })
            
            # 修复：正确更新FL30及以下所有高度的CAS值
            for i in range(fl030_index, len(new_df)):  # 注意这里改为fl030_index而不是fl030_index-1
                if new_df.iloc[i]['CAS(kt)'] > 220:
                    new_df.at[new_df.index[i], 'CAS(kt)'] = 220.0  # 使用正确的索引
                    # 同时更新Speed Mode显示
                    new_df.at[new_df.index[i], 'Speed Mode'] = 'CAS 220kt'
            
            horizontal_distance[fl030_index:] += decel_dist
            time_elapsed[fl030_index:] += decel_time
            fuel_consumption[fl030_index:] += decel_fuel

def apply_deceleration_segments(basic_summary, basic_df, flight_levels, 
                               high_cas, low_cas=None, low_cas_fl=100, 
                               print_details=True):
    """
    Apply all deceleration segments to the basic descent profile
    """
    # Copy original data
    new_df = basic_df.copy()
    
    # Get original cumulative data
    horizontal_distance = new_df['Cumulative Distance(nm)'].values.copy()
    time_elapsed = new_df['Cumulative Time(s)'].values.copy()
    fuel_consumption = new_df['Cumulative Fuel(kg)'].values.copy()
    
    # Create deceleration segment record list
    decel_segments = []
    
    # Apply various deceleration segments
    fl100_index = apply_fl100_deceleration(decel_segments, new_df, flight_levels, 
                                         horizontal_distance, time_elapsed, fuel_consumption)
    
    apply_profile_deceleration(decel_segments, new_df, flight_levels, high_cas, low_cas, 
                             low_cas_fl, fl100_index, horizontal_distance, time_elapsed, fuel_consumption)
    
    apply_approach_deceleration(decel_segments, new_df, flight_levels, 
                              horizontal_distance, time_elapsed, fuel_consumption)
    
    # Update cumulative data in DataFrame
    new_df['Cumulative Distance(nm)'] = [round(d, 1) for d in horizontal_distance]
    new_df['Cumulative Time(s)'] = [round(t, 0) for t in time_elapsed]
    new_df['Cumulative Fuel(kg)'] = [round(f, 1) for f in fuel_consumption]
    
    if print_details:
        print_deceleration_segments_table(decel_segments)
        print_final_profile_table(new_df)
    
    # Calculate new summary information
    total_distance = horizontal_distance[-1]
    total_time = time_elapsed[-1]
    total_fuel = fuel_consumption[-1]
    total_altitude_change = (flight_levels[0] - flight_levels[-1]) * 100
    avg_ft_per_nm = total_altitude_change / total_distance if total_distance > 0 else 0
    
    new_summary = {
        "Profile": basic_summary["Profile"], # + " (with deceleration segments)",
        "Descent Distance (nm)": round(total_distance, 1),
        "Descent Time (s)": round(total_time, 0),
        "Fuel Consumption (kg)": round(total_fuel, 1),
        "Average Fuel Flow (kg/h)": round(total_fuel/(total_time/3600), 1) if total_time > 0 else 0,
        "Average Descent Gradient (%)": round(total_altitude_change/6076.12/total_distance*100, 2) if total_distance > 0 else 0,
        "Altitude-to-Distance Ratio (ft/nm)": round(avg_ft_per_nm, 1)
    }
    
    if print_details:
        print_final_summary(new_summary, basic_summary)
    
    return new_summary, new_df, decel_segments

def print_basic_profile_table(df, profile_name):
    """Print basic descent profile table"""
    print(f"\nBasic Descent Data - {profile_name}:")
    print("-" * 165)
    
    # Select key columns to display
    display_columns = [
        'FL', 'Speed Mode', 'Mach', 'CAS(kt)', 'TAS(kt)', 
        'Descent Rate(ft/min)', 'Descent Gradient(%)', 'Alt-Dist Ratio(ft/nm)',
        'Fuel Flow(kg/h)', 'Cumulative Distance(nm)', 'Cumulative Time(s)', 'Cumulative Fuel(kg)'
    ]
    
    # Print header
    header = ""
    for col in display_columns:
        if col in ['FL', 'Mach', 'CAS(kt)', 'TAS(kt)']:
            header += f"{col:>8}"
        elif col in ['Speed Mode']:
            header += f"{col:>12}"
        elif col in ['Descent Rate(ft/min)', 'Descent Gradient(%)', 'Alt-Dist Ratio(ft/nm)', 'Fuel Flow(kg/h)']:
            header += f"{col:>12}"
        else:
            header += f"{col:>14}"
    print(header)
    print("-" * 165)
    
    # Print data rows
    for _, row in df.iterrows():
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
            elif col in ['Descent Gradient(%)']:
                line += f"{value:>12.2f}"
            elif col in ['Fuel Flow(kg/h)']:
                line += f"{value:>12.1f}"
            else:
                line += f"{value:>14.1f}"
        print(line)
    
    print("-" * 165)

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
        print(line)
    
    print("-" * 180)

def print_summary(summary):
    """Print descent profile summary (showing both seconds and minutes)"""
    print(f"\nDescent Profile Summary:")
    print(f"Total Descent Distance: {summary['Descent Distance (nm)']} nm")
    print(f"Total Descent Time: {summary['Descent Time (s)']} seconds ({summary['Descent Time (s)']/60:.1f} minutes)")
    print(f"Total Fuel Consumption: {summary['Fuel Consumption (kg)']} kg")
    print(f"Average Fuel Flow: {summary['Average Fuel Flow (kg/h)']} kg/h")
    print(f"Average Descent Gradient: {summary['Average Descent Gradient (%)']} %")
    print(f"Altitude-Distance Ratio: {summary['Altitude-to-Distance Ratio (ft/nm)']} ft/nm")
    print("=" * 80)

def print_final_summary(new_summary, basic_summary):
    """Print final summary information, including comparison with basic profile"""
    print(f"\nDescent Profile Summary after Adding Deceleration Segments:")
    distance_increase = new_summary['Descent Distance (nm)'] - basic_summary['Descent Distance (nm)']
    time_increase = new_summary['Descent Time (s)'] - basic_summary['Descent Time (s)']
    fuel_increase = new_summary['Fuel Consumption (kg)'] - basic_summary['Fuel Consumption (kg)']
    
    print(f"Total Descent Distance: {new_summary['Descent Distance (nm)']} nm (increased by {distance_increase:.1f} nm)")
    print(f"Total Descent Time: {new_summary['Descent Time (s)']} seconds ({new_summary['Descent Time (s)']/60:.1f} minutes) (increased by {time_increase:.0f} sec/{time_increase/60:.1f} min)")
    print(f"Total Fuel Consumption: {new_summary['Fuel Consumption (kg)']} kg (increased by {fuel_increase:.1f} kg)")
    print(f"Average Descent Gradient: {new_summary['Average Descent Gradient (%)']} %")
    print(f"Altitude-Distance Ratio: {new_summary['Altitude-to-Distance Ratio (ft/nm)']} ft/nm")
    print("=" * 80)

def calculate_complete_descent_profile(cruise_fl, target_fl, aircraft_mass, 
                                     descent_mach, high_cas, ac_model, 
                                     low_cas=None, low_cas_fl=100, 
                                     constant_cas=None, include_deceleration=True,
                                     print_details=True):
    """
    Calculate complete descent profile (including basic profile and deceleration segments)
    
    Parameters:
    cruise_fl: Cruise flight level (FL)
    target_fl: Target flight level (FL)
    aircraft_mass: Aircraft weight (kg)
    descent_mach: Descent Mach number
    high_cas: High altitude CAS (kt)
    ac_model: Aircraft model
    low_cas: Low altitude CAS (kt)
    low_cas_fl: Flight level where low altitude CAS begins (FL)
    constant_cas: Constant CAS descent speed (kt)
    include_deceleration: Whether to include deceleration segments
    print_details: Whether to print detailed information
    
    Returns:
    basic_summary, final_summary, basic_df, final_df, decel_segments
    """
    # Calculate basic descent profile
    basic_summary, basic_df, flight_levels = calculate_basic_descent_profile(
        cruise_fl, target_fl, aircraft_mass, descent_mach, high_cas, ac_model,
        low_cas, low_cas_fl, constant_cas, print_details
    )
    
    if include_deceleration:
        # Add deceleration segments
        final_summary, final_df, decel_segments = apply_deceleration_segments(
            basic_summary, basic_df, flight_levels, high_cas, low_cas, low_cas_fl, print_details
        )
        return basic_summary, final_summary, basic_df, final_df, decel_segments
    else:
        return basic_summary, None, basic_df, None, []
    
 ### Example code to use ###

# basic_summary, final_summary, basic_df, final_df, decel_segments = calculate_complete_descent_profile(
#         cruise_fl=370,
#         target_fl=30,
#         aircraft_mass=60000,
#         descent_mach=0.73,
#         high_cas=250,
#         ac_model="A320-232",
#         low_cas=220,
#         low_cas_fl=0,
#         include_deceleration=True,
#         print_details=True
#     )

basic_summary, final_summary, basic_df, final_df, decel_segments = calculate_complete_descent_profile(
        cruise_fl=370,
        target_fl=30,
        aircraft_mass=60000,
        descent_mach=0.80,
        high_cas=310,
        ac_model="A320-232",
        low_cas=0,
        low_cas_fl= 0,
        include_deceleration=True,
        print_details=True
    )
