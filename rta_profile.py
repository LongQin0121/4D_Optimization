from eta_window import origin_fl, target_fl, aircraft_mass, standard_route_length, ac_model, tolerance   
from bada_dis_time import calculate_descent_profile
import matplotlib.pyplot as plt
import Utility 
import A320
# MLW: 64500 kg,l = "A320-232"


###############################################
##  Step 3: Descide RTA within ETA window    ##
###############################################

rta=1896


#####################################################
##  Step 4: Find the profile that meet the RTA     ##
#####################################################

suitable_profiles = A320.find_profile_for_rta(
        origin_fl=origin_fl,
        target_fl=target_fl,
        aircraft_mass=aircraft_mass,
        ac_model=ac_model,
        standard_route_length=standard_route_length ,
        rta=rta,
        tolerance=tolerance,
        print_details=False      # Testing profile 38/42: 0.77M/285kt/220kt@FL50   ETA: 1844.9s, Difference from target: 55.1s
    )

params_rta = suitable_profiles[0]["params"]
eta = suitable_profiles[0]['eta']
cruise_distance = suitable_profiles[0]['cruise_distance'] 
cruise_time = suitable_profiles[0]['cruise_time']

print(
    f"Selected Profile: {params_rta}.\n"
    f"The estimated time of arrival (ETA) for Selected Profile is {suitable_profiles[0]['eta']} seconds.\n"
    f"The cruise distance is {suitable_profiles[0]['cruise_distance']} nm,"
    f"and the cruise time is {suitable_profiles[0]['cruise_time']} seconds."
)


#############################################################################
##  Step 5: Calculate the profile details of the ETA that meets the RTA    ##
#############################################################################

summary, df, decel_segments = calculate_descent_profile(
    cruise_fl=origin_fl,           
    target_fl=target_fl,             #
    aircraft_mass=aircraft_mass,      # 
    ac_model=ac_model,      # 
    descent_mach=params_rta['descent_mach'],
    high_cas=params_rta['high_cas'],
    intermediate_cas=params_rta['intermediate_cas'],
    intermediate_fl=params_rta['intermediate_fl'],
    print_details=False        # print details of summary, df, decel_segments
)


########################################################################
##  Step 6: PLOT the profile details of the ETA that meets the RTA    ##
########################################################################

fig, ax1, ax2 = Utility.plot_from_summary_and_df_with_dual_xaxis(
    summary, df, 
    standard_route_length=standard_route_length, 
    cruise_distance=cruise_distance,
    cruise_time=cruise_time,
    eta=eta,
    cruise_fl = origin_fl,
    figsize=(10, 8)
)
# plt.savefig("descent_profile.pdf", format="pdf", bbox_inches="tight")
plt.show()
