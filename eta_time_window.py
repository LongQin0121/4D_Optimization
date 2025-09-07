import Utility 
import A320

eta_window_all, min_profile, max_profile = A320.calculate_eta_window(
    origin_fl=370,
    target_fl=30,
    aircraft_mass=60000,
    ac_model="A320-232",
    standard_route_length=200,
    print_details=False
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
#     target_eta = 1900.0  # 目标RTA为1900秒
#     tolerance = 10.0     # 允许误差10    
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
        print_details=False
    )

params_rta = suitable_profiles[0]["params"]
print(params_rta)


##############################
#
# 示例: 0.73M/270kt，中间减速到220kt@FL50
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




# 调用函数，同时传入字典中的参数和其他必需参数
summary, df, decel_segments = calculate_descent_profile(
    cruise_fl=370,           
    target_fl=30,             #
    aircraft_mass=60000,      # 
    ac_model="A320-232",      # 
    descent_mach=params_rta['descent_mach'],
    high_cas=params_rta['high_cas'],
    intermediate_cas=params_rta['intermediate_cas'],
    intermediate_fl=params_rta['intermediate_fl'],
    print_details=True     #
)