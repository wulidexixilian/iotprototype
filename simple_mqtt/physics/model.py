import json


class PhysicsObject:
    # abstract father class for all physic abstractions
    def __init__(self):
        pass

    def bind(self):
        pass

    def update(self):
        pass

    def diagnose(self):
        pass

    def beat(self, ts):
        pass

    def to_dict(self):
        """
        convert the object into a dict
        :return:
        """
        d = dict()
        # check each attribute
        for key in self.__dict__:
            sub_obj = self.__dict__[key]
            if 'to_dict' in sub_obj.__dir__():
                # if this attribute is a physic model object, call its to_dict() method to step into it
                d[key] = sub_obj.to_dict()
            elif isinstance(sub_obj, list):
                # if this attribute is a list, check it one by one with the same logic
                d[key] = []
                for item in sub_obj:
                    if 'to_dict' in item.__dir__():
                        d[key].append(item.to_dict())
                    else:
                        d[key].append(item)
            else:
                # if this attribute is a basic data, add this to dict
                d[key] = sub_obj
        return d

    def to_json(self):
        d = self.to_dict()
        j = json.dumps(d, sort_keys=True, indent=4)
        return j


class PressureNode(PhysicsObject):
    def __init__(self):
        """
        initialize a hydraulic node, which maintains data of pressure,
        """
        self._pressure = 1

    @property
    def pressure(self):
        return self._pressure
        pass


class Rotor(PhysicsObject):
    def __init__(self):
        """
        initialize a basic rotation element
        """
        self._omega = 0

    @property
    def omega(self):
        return self.omega

    @omega.setter
    def omega(self, value):
        self._omega = value


class Motor(PhysicsObject):
    def __init__(self):
        """
        initialize an electrical motor
        """
        self._rotor = Rotor()
        self._temperature = None

    @property
    def omega(self):
        return self._rotor.omega

    @property
    def temperature(self):
        return self._temperature


class Tank(PhysicsObject):
    def __init__(self):
        self._level = None
        self._level_state = 0
        self._temperature = None
        self._cleaness = None


class Pump(PhysicsObject):
    def __init__(self):
        """
        initialize a hydraulic pump, which generate
        """
        self._port_s = PressureNode()
        self._port_p = PressureNode()
        self._port_l = PressureNode()
        self._rotor = Rotor()
        self._displacement_max = 0
        self._displacement_factor_cmd = 0
        self._displacement_factor_act = 0
        self._leakage_factor = 0
        self._friction_tau = 0
        self._temperature = None

    @property
    def displacement(self):
        """

        :return: actual displacement
        """
        return self._displacement_factor_act * self._displacement_max

    @property
    def flow(self):
        """
        flow rate in IS
        :return:
        """
        return self._rotor.omega * self.displacement

    @property
    def tau(self):
        """
        drive torque
        :return:
        """
        pressure_delta = self._outlet.pressure - self._intake.pressure

        return pressure_delta * self.displacement / 62.8 + self._friction_tau

    @property
    def temperature(self):
        return self._temperature


class Source(PhysicsObject):
    def __init__(self):
        """
        Initialization of hydraulic power source. It includes information of tank, pump, and relevant circuits.
        """
        self._pump = Pump()
        self._motor = Motor()
        self._tank = Tank()


class Valve(PhysicsObject):
    def __init__(self, type, port_num, state_num):
        self._spool_position = 0
        self._spool_cmd = 0


class Cylinder(PhysicsObject):
    def __init__(self):
        self._position = 0
        self._pressure_a = PressureNode()
        self._pressure_b = PressureNode()

    @property
    def pos(self):
        return self._position

    @property
    def p_a(self):
        return self._pressure_a

    @property
    def p_b(self):
        return self._pressure_b

    @property
    def vel(self):
        pass


class Edge(PhysicsObject):
    def __init__(self):
        self._pressure_1 = PressureNode()
        self._pressure_2 = PressureNode()
        self._open = None

    @property
    def flow(self):
        p_delta = self._pressure_2.pressure - self._pressure_1.pressures
        q = p_delta * self._open ** 0.5
        return q


class Valve(PhysicsObject):
    def __init__(self, type='proportional', port_num=4, state_num=3):
        self._ar_edge = []
        for idx in range(int(port_num/2)):
            self._ar_edge.append(Edge())

    def control(self):
        pass


class Manipulator(PhysicsObject):
    def __init__(self):
        """
        Initialization of a general hydraulic manipulator including actuators, like cylinder or motor,
        and control circuits like various valves
        """
        self._cylinder = Cylinder()
        self._valve = Valve()


class HydSystem(PhysicsObject):
    def __init__(self):
        self._manipulator = Manipulator()
        self._source = Source()
        self.variable = 1

