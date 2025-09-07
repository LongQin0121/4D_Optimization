import Utility 
import A320

eta_window_all, min_profile, max_profile = A320.calculate_eta_window(
    origin_fl=370,
    target_fl=30,
    aircraft_mass=60000,
    ac_model="A320-232",
    standard_route_length=200,
    print_details=False    #   Print details about the ETAmin and ETAmax
)
eta_window = eta_window_all['window']['eta_array']
print("ETA Window:", list(map(float, eta_window )),"seconds")

########################
#
#     origin_fl = 370
#     target_fl = 30
#     aircraft_mass = 60000
#     ac_model = "A320-232"
#     standard_route_length = 200
#     target_eta = 1900.0  # target RTA: 1900 seconds
#     tolerance = 10.0     # error: 10 seconds    
#
########################

suitable_profiles = A320.find_profile_for_rta(
        origin_fl=370,
        target_fl=30,
        aircraft_mass=60000,
        ac_model="A320-232",
        standard_route_length=200,
        target_eta=1900,
        tolerance=10,
        print_details=False       # Testing profile 38/42: 0.77M/285kt/220kt@FL50   ETA: 1844.9s, Difference from target: 55.1s
    )

params_rta = suitable_profiles[0]["params"]
print(params_rta)


##############################
#
# Example: 0.73M/270 kt, decelerating to 220 kt at FL50
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
###############################



from bada_dis_time import calculate_descent_profile

# Call the function, passing both the parameters from the dictionary and the other required argument
summary, df, decel_segments = calculate_descent_profile(
    cruise_fl=370,           
    target_fl=30,             #
    aircraft_mass=60000,      # 
    ac_model="A320-232",      # 
    descent_mach=params_rta['descent_mach'],
    high_cas=params_rta['high_cas'],
    intermediate_cas=params_rta['intermediate_cas'],
    intermediate_fl=params_rta['intermediate_fl'],
    print_details=True        # print details of summary, df, decel_segments
)

print(summary['Profile'])  #  'Descent Distance (nm)'   , 'Descent Time (s)' ,      'Fuel Consumption (kg)'

print(df.columns)    

    #  Index(['FL', 'Altitude(ft)', 'Speed Mode', 'Mach', 'CAS(kt)', 'TAS(kt)',
    #    'Descent Rate(ft/min)', 'Descent Rate(m/s)', 'Descent Angle(deg)',
    #    'Descent Gradient(%)', 'Alt-Dist Ratio(ft/nm)', 'ESF', 'Drag(N)',
    #    'Idle Thrust(N)', 'Fuel Flow(kg/h)', 'Fuel Flow(kg/s)',
    #    'Lift Coefficient', 'Drag Coefficient', 'Is Deceleration Point',
    #    'Cumulative Distance(nm)', 'Cumulative Time(s)', 'Cumulative Fuel(kg)'],
    #   dtype='object')