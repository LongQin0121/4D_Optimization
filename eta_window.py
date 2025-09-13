from bada_dis_time import calculate_descent_profile
import matplotlib.pyplot as plt
import Utility 
import A320

#############################################
##    Step 1: Define the hyperparameters   ##
#############################################

origin_fl = 370          # FL
target_fl = 30
aircraft_mass = 60000   # MLW: 64500 kg
ac_model = "A320-232"
standard_route_length = 200  # nm
tolerance = 10.0     # error: 10 seconds    


#############################################
##  Step 2: Calculate the ETA window       ##
#############################################

eta_window_all, min_profile, max_profile = A320.calculate_eta_window(
    origin_fl=origin_fl ,
    target_fl=target_fl ,
    aircraft_mass=aircraft_mass ,
    ac_model=ac_model,
    standard_route_length=standard_route_length ,
    print_details=False    #   Print details about the ETAmin and ETAmax
)
eta_window = eta_window_all['window']['eta_array']
print("ETA Window:", list(map(float, eta_window )),"seconds")
