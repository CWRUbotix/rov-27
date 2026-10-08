# Architecture Overview

There are three main areas where major components of our robot are run.

1. **Surface:** the competition laptop, router, and surface transceiver for the float.
2. **On-board the robot:** the Navigator, the Raspberry Pi, and the cameras.
3. **Float:** the Float board to control the float's depth.

This document will give an overview of the systems on the surface and the systems on the robot. Information about the float will be located in a separate document that will be created at a later date (the float is going through a major revision right now). Information about the surface transceiver will be included in the float document.

## Robot Operating System 2 (ROS 2)

ROS 2 is the main way that we run our code, and that we communicate between the surface and the Raspberry Pi onboard the robot. This is a very brief overview of some of the important ROS 2 systems we use, for more details look in the [Resources document](Resources.md).

### ROS Nodes

ROS allows for the creation of nodes, which are separate programs that can all be launched (started) at the same time and can communicate with each other as needed. Each ROS Node is responsible for one particular task, such as the GUI, processing images from the cameras, or sending controller commands to the robot. Having each ROS Node run separately with only specific forms of communication happening between Nodes helps us have better modularity and we can change the implementation of different Nodes without affecting others as long as we send the same messages as before. It also helps us to be able to have many people working on things at once because with each Node not likely to affect other Nodes, it makes it less likely for conflicting changes to happen from multiple people working on the same codebase.

### ROS Publishers and Subscribers

Publishers and subscribers are the main form of communication in ROS. A Node can create a publisher to send a message on a given _topic_. Any Node that wants to listen to those messages can create a subscriber on that same topic so that they will receive any of that type of message. There can be any number of publishers and subscribers for each possible topic.

### ROS Services

We use ROS Services less often than we use publishers and subscribers, however we still do use them for certain types of communication. Similar to publishers and subscribers, actions have a topic that they send messages on. However, unlike how publishers do not receive any feedback from the subscribers, services require a response. The first message sent on a service is called a Request, and there can be many nodes that can send a request on the same topic. However, the request can only be received by one Node that has a _server_ for that topic. That server will send a response to the request. Some examples of where we use this is for arming our robot, where the GUI or controller can send a request to arm, and it receives a response that the request was successfully received.

## Surface

The surface is where much of the heavy computing for the robot is handled because most of that is handled by the competition laptop. This is where the Operator is able to run our main GUI, the pilot is able to view cameras and control the robot, and where Operator tasks are handled.

### Competition Laptop

The competition laptop is plugged into the router, and a second monitor, so that the Operator and Pilot can each have a separate UI. There are many different ROS Nodes that run on the competition laptop.

- **flight_control:** This Node takes input from our controller and uses that to send commands to the robot on how it should move.
- **gui:** This Node controls the display of both our pilot and operator GUIs.
- **luxonis_cam:** This Node controls all communication with our stereo depth camera (made by Luxonis).
- **rov_flir:** This Node controls all communication with our forward and down cameras (made by FLIR).
- **rov_gazebo:** This Node controls our simulation of the robot (currently not working).
- **transciever:** This Node controls communication with the surface trainceiver that recieves information from the float.

## On-board the robot

### Blue Robotics Navigator

The Navigator is actually a board that is on top of the Raspberry Pi in the robot. The computing for it is actually done on the Raspberry Pi, however, we often refer to anything that is not a ROS Node that is running on the Raspberry Pi to be the Navigator. The Navigator is the flight computer that we use to control our ROV. A flight computer is able to receive commands such as "move forwards" and interpret what to do with the motors to make that movement happen. It has a representation of our motor layout to allow this to happen. The Navigator runs using BlueOS, which we can access an interface for on the competition laptop, and it allows for setting that motor layout as well as other parameters. Ports on the Navigator are usually controlled through BlueOS settings and are communicated with through Mavlink (talked about more later). Currently the systems that we have that are controlled by the navigator are the thrusters, and the manipulators, however we can connect other systems to the navigaot using the ports on top of it.

### Raspberry Pi

When we refer to things running on the Pi, we usually are referencing the ROS Nodes that are running on the Pi. This is controlled through a BlueOS extension, and that means that we need to use the BlueOS interface to access their terminals directly. Currently, the nodes running on the Pi are:

- **pi_info:** sends information about the Pi, such as it's current IP address and a heartbeat message to the surface.
- **pi_main:** does initial setup on the Pi when it boots.

### Cameras

Our cameras all have some amount of onboard compute, and we communicate with them separately from how we communicate to the Pi. There are surface ROS nodes in charge of that communication.

## Communication

Communication between the surface and the robot is done through an ethernet cable in the tether. The cameras each have their own IP address and are communicated to according to their respective libraries. The Pi and Navigator are communicated to through ethernet as well, and they have one IP address on the router that they share. However, while they are communicated to with the same IP address, they use different message protocols.

### ROS

Communication from the ROS Nodes running on the Pi is done through ROS. The ROS Nodes publish information, and Nodes on the surface receive that information. Because the surface and Pi are on the same network through the router, ROS is able to easily communicate between those Nodes.

### Mavlink

Communication to the Navigator is done through a protocol called Mavlink. This protocol is frequently used when communicating with flight computers. It is able to send different types of messages, such as movement messages that can say to move in different directions, or servo or relay (manipulator) control messages that say how a servo or relay should move. This also allows for reading information from the sensors that are plugged into the Navigator.

## Conclusion

This is just a brief overview of our main systems, for more in depth information, see the READMEs for the different ROS Nodes, and the documentation linked in the [Resources document](Resources.md)
