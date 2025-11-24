
while True:
    #send_thrust_to_pitch(servo_max);
    #send_thrust_to_esc(servo_max,0,1);
    input = raw_input("Thruster value:")
    thruster = input[0:1]
    val = input[1:4]

    if(thruster.upper() == "L"):
        # blah
        print("Left:"+val);
    if(thruster.upper() == "R"):
        # blah
        print("Right:" + val);
    if(thruster.upper() == "T"):
        # blah
        print("Tail:" + val);
    if(thruster.upper() == "A"):
        # send to all
        print("All:" + val);
    if(thruster.upper() == "N"):
        # send neutral to all
        print("Neutral.");



