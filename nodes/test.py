#!/usr/bin/env python

import rospy
from test_module import Test_module
import math
from std_srvs.srv import Empty, SetBool, SetBoolResponse


def callback():
    print 'hello'
    if True :
        print "Hello 1"
        if True:
            print "Hello 2"
            break
        print "Hello 3"
    print "Final Hello"

def server():
    rospy.init_node('server')
    s = rospy.Service('test', Empty, callback)
    rospy.spin()

if __name__ == "__main__":
    server()
