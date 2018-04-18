#!/usr/bin/env python

import rospy
import csv
import math


class Wall_Follower:

    def __init__(self, ir_bottom_pid, ir_top_pid, imu_wall_pid, imu_corner_pid,
                 motor_srv, cns_driver):

        self.ir_bottom_pid = ir_bottom_pid
        self.ir_top_pid = ir_top_pid
        self.imu_wall_pid = imu_wall_pid
        self.imu_corner_pid = imu_corner_pid
        self.motor_srv = motor_srv
        self.cns_driver = cns_driver
        self.motor_speed = 6400

        self.top_c_min = 75
        self.top_c_max = 300
        self.bottom_c_min = 700
        self.bottom_d_min = 90
        self.bottom_d_max = 700
        self.wall_speed = 6700
        self.door_speed = 6250
        self.corner_speed = 7000
        self.near_corner_speed = 4500
        self.near_corner_stopped_speed = 6200
        self.acceleration_min = 0.001
        self.doorways_seen_threshold = 0

        self.write_data = False

        # used for recording data
        if self.write_data:
            print "OPENING CSV"
            csv_out = open("/home/odroid/ros_ws/src/advanced_robotics_team6/data/ir_course_data_blockedwindow_1.csv", 'a')
            # csv_out = open("ir_course_data_doorway1.csv", 'a')
            self.writer = csv.writer(csv_out)

        self.imu_corner_pid.imu_setpoint()
        self.imu_wall_pid.imu_setpoint(self.imu_corner_pid.setpoint.data)
        #self.ir_bottom_pid.ir_setpoint(125)
        self.ir_top_pid.ir_setpoint(130)

        self.motor_srv(6450)
        rospy.sleep(0.5)

        # Set forward speed
        self.motor_srv(6400)
        print "MOTOR SPEED: ", self.motor_speed

        self.state = "wall_follow"
        self.ir_top.ignore = True
        self.imu_wall_pid.ignore = True
        self.imu_corner_pid.ignore = True
        self.imu_corner_pid.turns_completed = 0
        self.time_since_turn = rospy.get_time()

        self.previous_state = self.state

    def execute(self):
        #set speeds for different states
        if self.previous_state != self.state:
            if self.state == 'wall_follow':
                self.motor_srv(self.motor_speed)
            elif self.state == 'corner':
                self.motor_srv(self.corner_speed)
            elif self.state == 'near_corner':
                self.motor_srv(self.near_corner_speed)
            elif self.state == 'near_corner_stopped':
                self.motor_srv(self.near_corner_stopped_speed)
            else:
                self.motor_srv(self.door_speed)

        if len(self.imu_corner_pid.reported_states) < 4:
            return 0
        ir_top = self.ir_top_pid.state.data
        # define setpoint error values for state switching logic
        ir_bottom_error = math.fabs(self.ir_bottom_pid.setpoint.data - self.ir_bottom_pid.state.data)
        imu_wall_error = math.fabs(self.imu_wall_pid.setpoint.data - self.imu_corner_pid.state.data)
        imu_corner_error = math.fabs(self.imu_corner_pid.setpoint.data - self.imu_corner_pid.state.data)

        # finite differencing on state to estimate derivative (divide by timestep?)

        ir_bottom_diff = math.fabs(self.ir_bottom_pid.state.data - self.ir_bottom_pid.reported_states[-2])
        ir_top_diff = math.fabs(self.ir_top_pid.state.data - self.ir_top_pid.reported_states[-2])
        ir_top_difference = self.ir_top_pid.state.data - self.ir_top_pid.reported_states[-2]
        imu_wall_diff = math.fabs(self.imu_wall_pid.state.data - self.imu_corner_pid.reported_states[-2])
        imu_corner_diff = math.fabs(self.imu_corner_pid.state.data - self.imu_corner_pid.reported_states[-2])

        ir_bottom_average_error = math.fabs(self.ir_bottom_pid.setpoint.data - (self.ir_bottom_pid.reported_states[-1] + self.ir_bottom_pid.reported_states[-2] + self.ir_bottom_pid.reported_states[-3])/3)
        x_accel = self.cns_driver['linear_acceleration']['x'][-1]
        y_accel = self.cns_driver['linear_acceleration']['y'][-1]
        if self.write_data:
            print "WRITING DATA"
            self.writer.writerow([ir_bottom_error, ir_top_error, ir_bottom_diff, ir_top_diff])

        if self.state == 'wall_follow':
            print "WALL-FOLLOW"
            rospy.loginfo("ir_bottom_diff:\t%f", ir_bottom_diff)
            rospy.loginfo("ir_top_diff:\t%f", ir_top_diff)
            rospy.loginfo("ir_bottom_error:\t%f",ir_bottom_error)
            rospy.loginfo("ir_top_error:\t%f",ir_top_error)
            #corner near state
            if ir_bottom_error < 200 and ir_top < 300 and ir_top_difference < 0 \
             and self.imu_corner_pid.doorways_seen > self.doorways_seen_threshold \
             and self.imu_corner_pid.turns_completed < 2 and imu_corner_error < pi/4 \
             and ir_top_difference > -200:
                print "CORNER DETECTED"
                ir_bottom_pid.ignore = True
                imu_wall_pid.ignore = True      # don't know of any reason this should be False at this poin
                # enable imu_corner_pid
                imu_corner_pid.ignore = False
                imu_setpoint = imu_wall_pid.setpoint.data - math.radians(90)
                print "set imu setpoint to 90"
                imu_wall_pid.imu_setpoint(imu_setpoint)
                imu_corner_pid.imu_setpoint(imu_setpoint)
                robot["state"] = 'corner'
            # either top or bottom IR has detected doorway
            elif ir_top_error > self.top_c_max and (ir_bottom_error > self.bottom_d_min and \
        ir_bottom_error < self.bottom_d_max and ir_bottom_diff > 50):
                print "DOORWAY DETECTED"
                self.imu_corner_pid.doorways_seen += 1
                # ignore IR sensor that has detected doorway
                self.ir_bottom_pid.ignore = True
                self.ir_top_pid.ignore = True

                # use imu wall-following PID controller
                self.imu_wall_pid.ignore = False
                self.state = 'doorway'

            else:
                #protect against entering or exiting a corner
                #if ir_bottom_error < 5:
                    # reset IMU setpoint for cornering task
                    #imu_setpoint = 0
                    #headings = self.imu_wall_pid.recorded_states[:]
                    #for i in range(-1,-9,-1):
                        #imu_setpoint = imu_setpoint + headings[i]/8

                    #self.imu_wall_pid.imu_setpoint(imu_setpoint)
                    #self.imu_corner_pid.imu_setpoint(imu_setpoint)

                if ir_bottom_error < self.bottom_c_min and ir_top > self.top_c_max:
                    self.ir_bottom_pid.ignore = False
                elif ir_bottom_error > self.bottom_c_min:
                    self.ir_bottom_pid.ignore = True
                    print "ignoring bottom IR while wall following"

        elif self.state == 'doorway':
            print "DOORWAY"
            rospy.loginfo("ir_bottom_diff:\t%f", ir_bottom_diff)
            rospy.loginfo("ir_top_diff:\t%f", ir_top_diff)
            rospy.loginfo("ir_bottom_error:\t%f", ir_bottom_error)
            rospy.loginfo("ir_top_error:\t%f", ir_top_error)

            #if ir_top_error > CORNER_THRESHOLD:
                #ir_top_pid.ignore = True
                #robot["state"] = 'wall_follow'
                #print "exit becasue top corner threshold"
            if  ir_bottom_error > self.bottom_c_min and ir_top < self.top_c_max and \
        imu_corner_pid.turns_completed < 2 and ir_top_diff < 100 and ir_bottom_diff > 1000:
                self.imu_corner_pid.ignore = False
                self.imu_wall_pid.ignore = True
                imu_setpoint = self.imu_wall_pid.recorded_states[-1] - math.radians(90)
                self.imu_wall_pid.imu_setpoint(imu_setpoint)
                self.imu_corner_pid.imu_setpoint(imu_setpoint)
                rospy.sleep(.001)
                self.state = 'corner'
                print "exit to corner because bottom corner threshold"


            elif ir_bottom_error < 50 and ir_bottom_diff < 30:
                self.ir_bottom_pid.ignore = False
                self.imu_wall_pid.ignore = True

                self.state = 'wall_follow'
                print "Exited Doorway with standard method"

        elif self.state == 'corner':
            print "CORNERING"
            rospy.loginfo("ir_bottom_state:\t%f", self.ir_bottom_pid.state.data)
            rospy.loginfo("ir_top_state:\t%f", self.ir_top_pid.state.data)
            rospy.loginfo("ir_bottom_setpoint:\t%f", self.ir_bottom_pid.setpoint.data)
            rospy.loginfo("ir_top_setpoint:\t%f", self.ir_top_pid.setpoint.data)
            rospy.loginfo("CORNERING:\t{}\t{}".format(math.degrees(self.imu_corner_pid.state.data), math.degrees(imu_corner_error)))
            #if imu_corner_error > math.radians(85) and ir_top_difference < 0 and ir_top_pid.state.data < ir_top_pid.setpoint.data :
            #ir_bottom_pid.ignore = False
            #    ir_top_pid.ignore = False
            #    imu_wall_pid.ignore = True
            #    imu_corner_pid.ignore = True
            #    robot["state"] = 'wall_follow'
            #    print "exited turn due to top IR getting closer"
            if imu_corner_error < math.pi/9 and y_accel < .001:
                print "REACHED IMU SETPOINT WITHIN IMU_THRESHOLD
                # both IR errors are less than corner state

                if ir_bottom_error < 150 and ir_bottom_diff < 10:


                    # turn top and bottom IR PID control back on
                    self.ir_bottom_pid.ignore = False
                    self.imu_wall_pid.ignore = True
                    self.imu_corner_pid.ignore = True

                    self.state = 'wall_follow'
                    self.imu_corner_pid.turns_completed += 1

        elif self.state == 'corner_near':
    		#enter corner
            if ir_bottom_error > self.bottom_c_min and ir_top < self.top_c_max and \
        imu_corner_pid.turns_completed < 2 and ir_top_diff < 100 and ir_bottom_diff > 1000:
                self.ir_bottom_pid.ignore = True
                self.imu_wall_pid.ignore = True
                self.imu_corner_pid.ignore = False
                self.state = 'corner'
    		#enter wall follow
            elif ir_bottom_error < 100 and ir_top > self.top_c_max and ir_bottom_diff < 30:
                self.imu_corner_pid.doorways_seen += 1
                self.ir_bottom_pid.ignore = False
                self.imu_wall_pid.ignore = True
                self.state = 'wall_follow'
                print "Exited corner near with standard method"
            elif x_accel < self.acceleration_min:
        		self.state = 'corner_near_stopped'

        elif self.state == 'corner_near_stopped':
            if ir_bottom_error > self.bottom_c_min and ir_top < self.top_c_max and \
        imu_corner_pid.turns_completed < 2 and ir_top_diff < 100 and ir_bottom_diff > 1000:
                self.ir_bottom_pid.ignore = True
                self.imu_wall_pid.ignore = True
                self.imu_corner_pid.ignore = False
                self.state = 'corner'
    		#enter wall follow
            elif ir_bottom_error < 100 and ir_top > self.top_c_max and ir_bottom_diff < 30:
                self.imu_corner_pid.doorways_seen += 1
                self.ir_bottom_pid.ignore = False
                self.imu_wall_pid.ignore = True
                self.state = 'wall_follow'
                print "Exited corner near with standard method"

        else:
            print "Entered default case in state machine."

        # Set steering command as average of steering commands that we want to use
        i = 0
        steering_cmd = 0
        if not self.ir_bottom_pid.ignore:
            i += 1
            steering_cmd += self.ir_bottom_pid.control_effort
            #rospy.loginfo("steering_cmd_bottom:\t{}".format(ir_bottom_pid.control_effort))

        if not self.imu_wall_pid.ignore:
            i += 1
            steering_cmd += self.imu_wall_pid.control_effort
            #rospy.loginfo("steering_cmd_wall:\t{}".format(imu_wall_pid.control_effort))

        if not self.imu_corner_pid.ignore:
            i += 1
            steering_cmd += self.imu_corner_pid.control_effort
            #rospy.loginfo("steering_cmd_corner:\t{}".format(imu_corner_pid.control_effort))

        steering_cmd /= i
        rospy.loginfo("steering_cmd:\t{}".format(steering_cmd))

        return steering_cmd


    def finish(self):
        pass