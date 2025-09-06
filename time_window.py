from bada_dis_time import calculate_complete_descent_profile
import Utility 
import A320


# Aircraft parameters
# cruise_fl = 370
# target_fl = 30
# aircraft_mass = 60000
# descent_mach = 0.73
# high_cas = 256
# ac_model = "A320-232"
# low_cas = 220
# low_cas_fl = 150



eta_min, eta_max, eta_min_profile, eta_max_profile = A320.calculate_eta_range(cruise_fl=370, target_fl=30, aircraft_mass=60000, 
                        ac_model="A320-232", standard_route_length=200)

# GOT windoW


# closest_match, closest_match['param'], closest_match['df']
best_profile  = A320.find_profile_for_rta(
    target_rta=1677.87,             # 目标到达时间1850秒
    tolerance=10,                # 15秒容忍误差
    cruise_fl=370,               # 巡航高度FL380
    target_fl=30,                # 目标高度FL20
    aircraft_mass=60000,         # 飞机质量58吨
    ac_model="A320-232",         # 飞机型号
    standard_route_length=200    # 220海里的航线长度
)
##  closest_match['param'], closest_match['df']
##
print(best_profile['df'].columns)
# print(best_profile['df']['Alt-Dist Ratio(ft/nm)'])


cols = [
    'FL', 'Altitude(ft)', 'Speed Mode', 'Mach', 'CAS(kt)', 'TAS(kt)',
    'Descent Gradient(%)', 'Alt-Dist Ratio(ft/nm)',
    'Cumulative Distance(nm)', 'Cumulative Time(s)', 'Cumulative Fuel(kg)'
]

print(best_profile['df'][cols])




# # Calculate cruise true airspeed and ground speed (assuming zero wind)
# tas = Utility.mach2tas_kt(flight_level=cruise_fl, mach=descent_mach, delta_temp=0)
# gs = round(tas, 1)


# # Calculate complete descent profile
# _, Param, _, df, _ = calculate_complete_descent_profile(
#     cruise_fl=cruise_fl,
#     target_fl=target_fl,
#     aircraft_mass=aircraft_mass,
#     descent_mach=descent_mach,
#     high_cas=high_cas,
#     ac_model=ac_model,
#     low_cas=low_cas,
#     low_cas_fl=low_cas_fl,
#     # include_deceleration=True,
#     print_details=False  # Set to False to avoid printing detailed information
# )

# # print(df.columns)
# # print(df['Alt-Dist Ratio(ft/nm)'])

# # Extract key descent parameters
# descent_profile = Param['Profile']
# descent_distance = Param['Descent Distance (nm)']
# descent_time = Param['Descent Time (s)']

# # Calculate total flight time
# standard_route_length = 200  # Replace with your actual fixed distance value (nm)
# cruise_distance = standard_route_length - descent_distance
# cruise_time = cruise_distance / gs * 3600  # Convert to seconds (gs is in knots)
# total_flight_time = cruise_time + descent_time  # Total time in seconds

# print(total_flight_time)
