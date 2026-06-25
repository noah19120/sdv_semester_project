import rclpy
from rclpy.node import Node
from std_msgs.msg import UInt8, Int16
from kuksa_client.grpc import VSSClient, Datapoint

class Ros2VssBridge(Node):
    def __init__(self, vss_client):
        super().__init__('ros2_vss_bridge')
        
        # Accept the pre-authenticated and connected live VSS gRPC client context
        self.vss_client = vss_client
        self.get_logger().info("Successfully hooked into active Kuksa Databroker gRPC channel context!")
        
        # Topic subscriptions
        self.sub_accel = self.create_subscription(UInt8, '/vehicle/chassis/accelerator', self.accel_cb, 10)
        self.sub_brake = self.create_subscription(UInt8, '/vehicle/chassis/brake', self.brake_cb, 10)
        self.sub_steer = self.create_subscription(Int16, '/vehicle/chassis/steering', self.steer_cb, 10)
        
    def accel_cb(self, msg):
        self.vss_client.set_current_values({
            'Vehicle.Chassis.Accelerator.PedalPosition': Datapoint(msg.data)
        })
        
    def brake_cb(self, msg):
        self.vss_client.set_current_values({
            'Vehicle.Chassis.Brake.PedalPosition': Datapoint(msg.data)
        })
        
    def steer_cb(self, msg):
        self.vss_client.set_current_values({
            'Vehicle.Chassis.SteeringWheel.Angle': Datapoint(msg.data)
        })

def main(args=None):
    rclpy.init(args=args)
    
    # Establish the connection inside a native python context manager wrapper
    # This automatically instantiates channels, manages stubs, and handles cleanup on shutdown
    with VSSClient('127.0.0.1', 55555) as client:
        node = Ros2VssBridge(vss_client=client)
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            
    rclpy.shutdown()

if __name__ == '__main__':
    main()