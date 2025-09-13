from bada_dis_time import calculate_descent_profile
import Utility

def calculate_eta_window(origin_fl, target_fl, aircraft_mass, ac_model, standard_route_length=200, print_details=False):
    """
    Calculate the time window (ETAmin and ETAmax) for descent process, including cruise segment
    
    Parameters:
    origin_fl: int - Initial flight level
    target_fl: int - Target flight level
    aircraft_mass: float - Aircraft mass (kg)
    ac_model: str - Aircraft model
    standard_route_length: float - Standard route total length (nm)
    print_details: bool - Whether to print detailed information
    
    Returns:
    dict: Dictionary containing ETAmin and ETAmax information
    """
    # Calculate ETAmin - using high-speed descent profile
    min_summary, min_df, min_decel = calculate_descent_profile(
        cruise_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        descent_mach=0.80,
        high_cas=310,
        print_details=False
    )
    
    # Calculate ETAmax - using low-speed descent profile
    max_summary, max_df, max_decel = calculate_descent_profile(
        cruise_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        descent_mach=0.73,
        high_cas=245,
        intermediate_cas=220,
        intermediate_fl=150,
        print_details=False
    )
    
    # Calculate ETAmin cruise segment
    min_descent_distance = min_summary["Descent Distance (nm)"]
    min_descent_time = round(min_summary["Descent Time (s)"], 1)  # Keep one decimal place
    
    # Calculate cruise true airspeed and ground speed (ETAmin)
    min_tas = Utility.mach2tas_kt(flight_level=origin_fl, mach=0.80)
    min_gs = round(min_tas, 1)
    
    min_cruise_distance = standard_route_length - min_descent_distance
    min_cruise_time = round(min_cruise_distance / min_gs * 3600, 1)  # Convert to seconds, keep one decimal place
    min_eta = round(min_cruise_time + min_descent_time, 1)
    
    # Calculate ETAmax cruise segment
    max_descent_distance = max_summary["Descent Distance (nm)"]
    max_descent_time = round(max_summary["Descent Time (s)"], 1)  # Keep one decimal place
    
    # Calculate cruise true airspeed and ground speed (ETAmax)
    max_tas = Utility.mach2tas_kt(flight_level=origin_fl, mach=0.73)
    max_gs = round(max_tas, 1)
    
    max_cruise_distance = standard_route_length - max_descent_distance
    max_cruise_time = round(max_cruise_distance / max_gs * 3600, 1)  # Convert to seconds, keep one decimal place
    max_eta = round(max_cruise_time + max_descent_time, 1)
    
    # Calculate time window
    window_seconds = round(max_eta - min_eta, 1)
    
    # Create ETAmin and ETAmax arrays
    eta_array = [min_eta, max_eta]
    
    # Create cruise distance array
    cruise_distance_array = [min_cruise_distance, max_cruise_distance]
    
    # Create result dictionary
    result = {
        "ETAmin": {
            "profile": min_summary["Profile"],
            "cruise_mach": 0.80,
            "cruise_tas_kt": min_tas,
            "cruise_gs_kt": min_gs,
            "cruise_distance_nm": min_cruise_distance,
            "cruise_time_seconds": min_cruise_time,
            "descent_distance_nm": min_descent_distance,
            "descent_time_seconds": min_descent_time,
            "total_time_seconds": min_eta,
            "fuel_kg": min_summary["Fuel Consumption (kg)"]
        },
        "ETAmax": {
            "profile": max_summary["Profile"],
            "cruise_mach": 0.73,
            "cruise_tas_kt": max_tas,
            "cruise_gs_kt": max_gs,
            "cruise_distance_nm": max_cruise_distance,
            "cruise_time_seconds": max_cruise_time,
            "descent_distance_nm": max_descent_distance,
            "descent_time_seconds": max_descent_time,
            "total_time_seconds": max_eta,
            "fuel_kg": max_summary["Fuel Consumption (kg)"]
        },
        "window": {
            "time_seconds": window_seconds,
            "standard_route_length": standard_route_length,
            "eta_array": eta_array,  # Add ETA array
            "cruise_distance_array": cruise_distance_array  # Add cruise distance array
        }
    }
    
    # Print results
    if print_details:
        print(f"\n{'='*100}")
        print(f"Full Route ETA Window Analysis: {ac_model}")
        print(f"{'='*100}")
        print(f"Initial Altitude: FL{origin_fl}")
        print(f"Target Altitude: FL{target_fl}")
        print(f"Aircraft Weight: {aircraft_mass/1000:.1f} tonnes")
        print(f"Standard Route Length: {standard_route_length} nm")
        print(f"{'='*100}")
        
        print(f"\nETAmin (Fastest Arrival Option):")
        print(f"  Flight Profile: {min_summary['Profile']}")
        print(f"  Cruise Mach: 0.80M")
        print(f"  Cruise Speed: {min_gs} kt")
        print(f"  Cruise Distance: {min_cruise_distance:.1f} nm")
        print(f"  Cruise Time: {min_cruise_time:.1f} seconds")
        print(f"  Descent Distance: {min_descent_distance:.1f} nm")
        print(f"  Descent Time: {min_descent_time:.1f} seconds")
        print(f"  Total Flight Time: {min_eta:.1f} seconds")
        print(f"  Descent Fuel: {min_summary['Fuel Consumption (kg)']:.1f} kg")
        
        print(f"\nETAmax (Slowest Arrival Option):")
        print(f"  Flight Profile: {max_summary['Profile']}")
        print(f"  Cruise Mach: 0.73M")
        print(f"  Cruise Speed: {max_gs} kt")
        print(f"  Cruise Distance: {max_cruise_distance:.1f} nm")
        print(f"  Cruise Time: {max_cruise_time:.1f} seconds")
        print(f"  Descent Distance: {max_descent_distance:.1f} nm")
        print(f"  Descent Time: {max_descent_time:.1f} seconds")
        print(f"  Total Flight Time: {max_eta:.1f} seconds")
        print(f"  Descent Fuel: {max_summary['Fuel Consumption (kg)']:.1f} kg")
        
        print(f"\nTime Window:")
        print(f"  Window Size: {window_seconds:.1f} seconds")
        print(f"  ETA Array: {eta_array}")  # Print ETA array
        print(f"  Cruise Distance Array: {cruise_distance_array}")  # Print cruise distance array
        print(f"{'='*100}")
    
    return result, min_df, max_df


# Usage example
# eta_result, min_profile, max_profile = calculate_eta_window(
#     origin_fl=370,
#     target_fl=30,
#     aircraft_mass=60000,
#     ac_model="A320-232",
#     standard_route_length=200
# )


from bada_dis_time import calculate_descent_profile
import Utility
import numpy as np


def find_profile_for_rta(origin_fl, target_fl, aircraft_mass, ac_model,
                        standard_route_length, rta, tolerance=10.0, max_profiles=5, print_details=False):
    """
    Intelligent search for descent profile parameters that meet target RTA
    
    Parameters:
    origin_fl: int - Initial flight level
    target_fl: int - Target flight level
    aircraft_mass: float - Aircraft mass (kg)
    ac_model: str - Aircraft model
    standard_route_length: float - Standard route total length (nm)
    rta: float - Target ETA (seconds)
    tolerance: float - Allowable ETA error (seconds)
    max_profiles: int - Maximum number of profiles to return
    
    Returns:
    list - List of descent profile parameters and corresponding ETAs that meet criteria
    """
    # First calculate baseline ETAmin and ETAmax to understand if RTA is within reasonable range
    min_result, min_df, min_decel = calculate_eta_window(
        origin_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        standard_route_length=standard_route_length,
        print_details=False
    )
    
    eta_min = min_result["ETAmin"]["total_time_seconds"]
    eta_max = min_result["ETAmax"]["total_time_seconds"]
    eta_window = eta_max - eta_min
    
    print(f"Baseline ETAmin: {eta_min:.1f}s, ETAmax: {eta_max:.1f}s")
    print(f"ETA Window: {eta_window:.1f}s")
    print(f"Target RTA: {rta:.1f}s, Allowable Error: ±{tolerance:.1f}s")
    
    # Check if target RTA is within feasible range
    if rta < eta_min - tolerance:
        print(f"Warning: Target RTA is {eta_min - rta:.1f}s smaller than minimum ETA")
        return []
    elif rta > eta_max + tolerance:
        print(f"Warning: Target RTA is {rta - eta_max:.1f}s larger than maximum ETA")
        return []
    
    # Generate intelligent parameter search space
    profile_params = generate_profile_params(eta_min, eta_max, rta)
    
    if print_details:
        print(f"\nGenerated {len(profile_params)} parameter combinations for search")
    
    print("\nStarting search for descent profiles that meet RTA...\n")
    
    # Store qualifying profiles
    suitable_profiles = []
    
    # Calculate actual ETA for each parameter combination
    for i, params in enumerate(profile_params):
        profile_str = format_profile_string(params)
        if print_details:
            print(f"Testing profile {i+1}/{len(profile_params)}: {profile_str}")
        
        try:
            # Calculate descent profile for current parameter combination
            descent_params = {
                "cruise_fl": origin_fl,
                "target_fl": target_fl,
                "aircraft_mass": aircraft_mass,
                "ac_model": ac_model,
                "descent_mach": params["descent_mach"],
                "high_cas": params["high_cas"],
                "print_details": False
            }
            
            # Add intermediate altitude and CAS to parameters if present
            if params["intermediate_fl"] is not None and params["intermediate_cas"] is not None:
                descent_params["intermediate_fl"] = params["intermediate_fl"]
                descent_params["intermediate_cas"] = params["intermediate_cas"]
            
            # Calculate descent profile
            summary, df, decel = calculate_descent_profile(**descent_params)
            
            # Calculate total ETA
            descent_distance = summary["Descent Distance (nm)"]
            descent_time = round(summary["Descent Time (s)"], 1)
            
            # Calculate cruise segment
            cruise_distance = standard_route_length - descent_distance
            cruise_tas = Utility.mach2tas_kt(flight_level=origin_fl, mach=params["descent_mach"])
            cruise_gs = round(cruise_tas, 1)
            cruise_time = round(cruise_distance / cruise_gs * 3600, 1)
            
            # Calculate total ETA
            total_eta = round(cruise_time + descent_time, 1)
            
            # Calculate difference from target ETA
            eta_diff = abs(total_eta - rta)
            
            if print_details:
                print(f"  ETA: {total_eta:.1f}s, Difference from target: {eta_diff:.1f}s")
            
            # Add to qualifying list if within tolerance
            if eta_diff <= tolerance:
                suitable_profiles.append({
                    "params": params,
                    "profile_str": profile_str,
                    "eta": total_eta,
                    "diff": eta_diff,
                    "descent_distance": descent_distance,
                    "descent_time": descent_time,
                    "cruise_distance": cruise_distance,
                    "cruise_time": cruise_time,
                    "fuel_kg": summary["Fuel Consumption (kg)"]
                })
                if print_details:
                    print(f"  ✓ Meets criteria!")
            else:
                if print_details:
                    print(f"  ✗ Outside tolerance range")
                
        except Exception as e:
            if print_details:
                print(f"  Calculation error: {e}")
    
    # Sort by difference from target ETA
    suitable_profiles.sort(key=lambda x: x["diff"])
    
    # Limit number of returned profiles
    suitable_profiles = suitable_profiles[:max_profiles]
    
    return suitable_profiles



def generate_profile_params(eta_min, eta_max, rta):
    """
    Intelligently generate descent profile parameter combinations based on target ETA position within ETA window
    
    Parameters:
    eta_min: float - Minimum ETA value (seconds)
    eta_max: float - Maximum ETA value (seconds)
    rta: float - Target ETA (seconds)
    
    Returns:
    list - List of parameter dictionaries
    """
    params_list = []
    
    # Calculate relative position of target ETA within ETA window (0.0 means close to ETAmin, 1.0 means close to ETAmax)
    relative_position = (rta - eta_min) / (eta_max - eta_min)
    
    # Adjust Mach number and CAS search range based on relative position
    if relative_position < 0.2:
        # Close to ETAmin, prioritize high Mach numbers and high CAS
        mach_values = [0.78, 0.79, 0.80]
        cas_ranges = {
            0.78: [290, 295, 300],
            0.79: [295, 300, 305],
            0.80: [300, 305, 310]
        }
        # Close to ETAmin, intermediate altitude may not be needed
        int_options = [
            (None, None),
            (220, 50),
            (220, 50)
        ]
    elif relative_position < 0.4:
        # Between ETAmin and midpoint, favor fast profiles
        mach_values = [0.76, 0.77, 0.78, 0.79]
        cas_ranges = {
            0.76: [275, 280, 285],
            0.77: [280, 285, 290, 295],
            0.78: [285, 290, 295],
            0.79: [290, 295, 300]
        }
        int_options = [
            (None, None),
            (220, 50),
            (220, 60)
        ]
    elif relative_position < 0.6:
        # Close to midpoint, moderate Mach numbers and CAS
        mach_values = [0.75, 0.76, 0.77]
        cas_ranges = {
            0.75: [265, 270, 275, 280],
            0.76: [270, 275, 280],
            0.77: [275, 280, 285]
        }
        int_options = [
            (None, None),
            (220, 50),
            (220, 60),
            (220, 80)
        ]
    elif relative_position < 0.8:
        # Between midpoint and ETAmax, favor slow profiles
        mach_values = [0.74, 0.75, 0.76]
        cas_ranges = {
            0.74: [250,255, 260],
            0.75: [255, 260, 265],
            0.76: [265, 270, 275]
        }
        int_options = [
            (220, 50),
            (220, 60),
            (220, 80),
            (220, 100)
        ]
    else:
        # Close to ETAmax, prioritize low Mach numbers and low CAS
        mach_values = [0.73, 0.74]
        cas_ranges = {
            0.73: [245, 250, 255],
            0.74: [250, 255, 260]
        }
        int_options = [
            (220, 60),
            (220, 80),
            (220, 100),
            (220, 120),
            (220, 130),
            (220, 150)
        ]
    
    # Generate parameter combinations
    for mach in mach_values:
        for cas in cas_ranges[mach]:
            for int_cas, int_fl in int_options:
                # Create parameter dictionary
                param = {
                    "descent_mach": mach,
                    "high_cas": cas,
                    "intermediate_cas": int_cas,
                    "intermediate_fl": int_fl
                }
                
                params_list.append(param)
    
    # Always add baseline configurations
    params_list.append({
        "descent_mach": 0.80,
        "high_cas": 310,
        "intermediate_cas": None,
        "intermediate_fl": None
    })
    
    params_list.append({
        "descent_mach": 0.73,
        "high_cas": 245,
        "intermediate_cas": 220,
        "intermediate_fl": 150
    })
    
    return params_list

def format_profile_string(params):
    """Format parameters into standard descent profile string representation"""
    mach = params["descent_mach"]
    high_cas = params["high_cas"]
    intermediate_cas = params["intermediate_cas"]
    intermediate_fl = params["intermediate_fl"]
    
    if intermediate_fl is None:
        return f"{mach:.2f}M/{high_cas}kt"
    else:
        return f"{mach:.2f}M/{high_cas}kt/{intermediate_cas}kt@FL{intermediate_fl}"

# Usage example
# if __name__ == "__main__":
#     # Set parameters
#     origin_fl = 370
#     target_fl = 30
#     aircraft_mass = 60000
#     ac_model = "A320-232"
#     standard_route_length = 200
#     rta = 1900.0  # Target RTA is 1900 seconds
#     tolerance = 10.0     # Allow 10 seconds error
    
#     # Find descent profiles that meet criteria
#     suitable_profiles = find_profile_for_rta(
#         origin_fl=origin_fl,
#         target_fl=target_fl,
#         aircraft_mass=aircraft_mass,
#         ac_model=ac_model,
#         standard_route_length=standard_route_length,
#         rta=rta,
#         tolerance=tolerance,
#          print_details=True
#     )
    
#     # Display results
#     print(f"\n{'='*80}")
#     print(f"Found {len(suitable_profiles)} descent profiles that meet target RTA:")
#     print(f"{'='*80}")
    
#     for i, profile in enumerate(suitable_profiles):
#         params = profile["params"]
#         print(f"\n{i+1}. Descent Profile: {profile['profile_str']}")
#         print(f"   ETA: {profile['eta']:.1f}s (Difference from target: {profile['diff']:.1f}s)")
#         print(f"   Cruise Mach: {params['descent_mach']:.2f}M")
#         print(f"   Cruise Distance: {profile['cruise_distance']:.1f} nm")
#         print(f"   Cruise Time: {profile['cruise_time']:.1f} seconds")
#         print(f"   Descent Distance: {profile['descent_distance']:.1f} nm")
#         print(f"   Descent Time: {profile['descent_time']:.1f} seconds")
#         print(f"   Fuel Consumption: {profile['fuel_kg']:.1f} kg")
    
#     print(f"\n{'='*80}")
    
#     # Save results as arrays
#     if suitable_profiles:
#         eta_array = [profile["eta"] for profile in suitable_profiles]
#         print(f"Qualifying ETA array: {eta_array}")
        
#         profile_array = [profile["profile_str"] for profile in suitable_profiles]
#         print(f"Qualifying profile array: {profile_array}")
        
#         # Save parameters of first best matching profile
#         best_profile = suitable_profiles[0]["params"]
#         print(f"Best matching profile parameters: {best_profile}")
#     else:
#         print("No descent profiles found that meet criteria")