import json
from collections import deque
import database as db_admin
# import mqtt_admin


class Data:
    def __init__(self, data_type='float', data_id=-1, ts=0.5, default_value=0, max_record_len=10000):
        self._type = data_type
        self._ts = ts
        self._id = data_id
        self._value = default_value
        self._time_stamp = None
        self._record = deque([], max_record_len)
        self._t_record = deque([], max_record_len)
        self._beat_counter = 0
        self._db = None

    def set_record(self):
        self._record.append(self.value)
        self._t_record.append(self.time_stamp)

    def update(self, new_package):
        self.value = new_package['value']
        self.time_stamp = new_package['time_stamp']
        self.set_record()
        pass

    def acquire(self, beat_period):
        self._beat_counter += beat_period
        if self._beat_counter >= self._ts:
            self._beat_counter = 0
            return self._id

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    @property
    def time_stamp(self):
        return self._time_stamp

    @time_stamp.setter
    def time_stamp(self, new_time):
        self._time_stamp = new_time

    @property
    def id(self):
        return self._id

    def assign_id(self, root_id, this_id):
        self._id = root_id + '$' + this_id

    def set_ts(self, ts):
        self._ts = ts


class Thing:
    # abstract father class for all physic abstractions
    def __init__(self):
        self._id = None

    def bind(self):
        pass

    def update(self, package):
        for key in self.__dict__:
            sub_obj = self.__dict__[key]
            if isinstance(sub_obj, Thing):
                sub_obj.update(package)
            elif isinstance(sub_obj, Data):
                if sub_obj.id in package:
                    sub_obj.update(package[sub_obj.id])
            elif isinstance(sub_obj, list):
                for idx, item in enumerate(sub_obj):
                    if isinstance(item, Thing):
                        item.update(package)
                    elif isinstance(item, Data):
                        item.update(package[item.id])
            else:
                pass
        self.process()

    def process(self):
        pass

    def diagnose(self):
        pass

    def acquire(self, ts):
        wish_list = []
        for key in self.__dict__:
            sub_obj = self.__dict__[key]
            if isinstance(sub_obj, Thing):
                wish_list += sub_obj.acquire(ts)
            elif isinstance(sub_obj, list):
                for item in sub_obj:
                    if isinstance(sub_obj, Thing):
                        wish_list += item.acquire(ts)
                    elif isinstance(item, Data):
                        data_to_get = item.acquire(ts)
                        if data_to_get is not None:
                            wish_list.append(data_to_get)
                    else:
                        # unexpection to be raised
                        pass
            elif isinstance(sub_obj, Data):
                data_to_get = sub_obj.acquire(ts)
                if data_to_get is not None:
                    wish_list.append(data_to_get)
            else:
                pass
        return wish_list

    def to_dict(self):
        """
        convert the object into a dict
        :return: a dict of all data of this node and all its sub-level nodes
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
                        value = sub_obj.value
                        time_stamp = sub_obj.time_stamp
                        element = {'value': value, 'time stamp': time_stamp}
                        d[key].append(element)
            elif isinstance(sub_obj, Data):
                # if this attribute is a basic data, add this to dict
                value = sub_obj.value
                time_stamp = sub_obj.time_stamp
                d[key] = {'value': value, 'time stamp': time_stamp}
            elif key is '_id' and isinstance(sub_obj, str):
                d[key] = sub_obj
            else:
                pass
        return d

    def to_json(self):
        d = self.to_dict()
        j = json.dumps(d, sort_keys=True, indent=4)
        return j

    def assign_id(self, root_id='', this_id='root'):
        self._id = root_id + '.' + this_id
        # check each attribute
        for key in self.__dict__:
            sub_obj = self.__dict__[key]
            if isinstance(sub_obj, Thing) or isinstance(sub_obj, Data):
                sub_obj.assign_id(self._id, key)
            elif isinstance(sub_obj, list):
                for idx, item in enumerate(sub_obj):
                    item.assign_id(self._id, key+'[{}]'.format(idx))
            else:
                pass


class PressureNode(Thing):
    def __init__(self):
        """
        initialize a hydraulic node, which maintains data of pressure,
        """
        self._pressure = Data(default_value=1)

    @property
    def pressure(self):
        return self._pressure.value

    @pressure.setter
    def pressure(self, value):
        self._pressure.value = value


class Rotor(Thing):
    def __init__(self):
        """
        initialize a basic rotation element
        """
        self._omega = Data(default_value=0)

    @property
    def omega(self):
        return self._omega.value

    @omega.setter
    def omega(self, value):
        self._omega.value = value


class Analog(Thing):
    def __init__(self, min_value=0, max_value=1, min_sig=4, max_sig=20):
        self._max_value = max_value
        self._min_value = min_value
        self._value_scale = None
        self._min_sig = min_sig
        self._max_sig = max_sig
        self._sig_scale = None
        self._signal = Data()

    @property
    def value(self):
        if self._value_scale is None:
            self._value_scale = self._max_value - self._min_value
        if self._sig_scale is None:
            self._sig_scale = self._max_sig - self._min_sig
        val = (self._signal - self._min_sig) / self._sig_scale * self._value_scale + self._min_value
        return val

    @property
    def signal(self):
        return self._signal

    @signal.setter
    def signal(self, sig):
        self._signal.value = sig


class PT(Thing):
    def __init__(self):
        self._temperature = Data(default_value=20)

    @property
    def temperature(self):
        return self._temperature.value


class Motor(Thing):
    def __init__(self):
        """
        initialize an electrical motor
        """
        self._rotor = Rotor()
        self._temperature_sensor = PT()

    @property
    def omega(self):
        return self._rotor.omega

    @property
    def temperature(self):
        return self._temperature_sensor.temperature


class Tank(Thing):
    def __init__(self):
        self._level = Analog()
        self._level_state = None
        self._temperature = PT()
        self._clean = Analog()


class Pump(Thing):
    def __init__(self, displacement=0):
        """
        initialize a hydraulic pump, which generate
        """
        self._port_s = PressureNode()
        self._port_p = PressureNode()
        self._port_l = PressureNode()
        self._rotor = Rotor()
        self._displacement_max = displacement
        self._displacement_factor_cmd = Analog()
        self._displacement_factor_act = Analog()
        self._leakage_factor = 0
        self._friction_tau = 0
        self._temperature = PT()

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


class Source(Thing):
    def __init__(self):
        """
        Initialization of hydraulic power source. It includes information of tank, pump, and relevant circuits.
        """
        self._pump = Pump()
        self._motor = Motor()
        self._tank = Tank()


class Valve(Thing):
    def __init__(self, type, port_num, state_num):
        self._spool_position = Analog()
        self._spool_cmd = Analog()


class Cylinder(Thing):
    def __init__(self):
        self._position = Analog()
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


class Edge(Thing):
    def __init__(self):
        self._pressure_1 = PressureNode()
        self._pressure_2 = PressureNode()
        self._open = Analog()

    @property
    def flow(self):
        p_delta = self._pressure_2.pressure - self._pressure_1.pressures
        q = p_delta * self._open ** 0.5
        return q


class Valve(Thing):
    def __init__(self, type='proportional', port_num=4, state_num=3):
        self._ar_edge = []
        for idx in range(int(port_num/2)):
            self._ar_edge.append(Edge())

    def control(self):
        pass


class Manipulator(Thing):
    def __init__(self):
        """
        Initialization of a general hydraulic manipulator including actuators, like cylinder or motor,
        and control circuits like various valves
        """
        self._cylinder = Cylinder()
        self._valve = Valve()


class HydSystem(Thing):
    def __init__(self):
        self._manipulator = Manipulator()
        self._source = Source()
        self.assign_id()

    # def beat(self, host='127.0.0.1', port=1885, ts=0.3,):
    #     wish_list = super(HydSystem, self).beat(ts)
    #     # if len(wish_list) > 0:
    #     #     mqtt_admin.client_beat.connect(host, port, 60)
    #     #     mqtt_admin.client_beat.publish('machine_state_request', payload=json.dumps({'wish_list': wish_list}))
    #     #     mqtt_admin.client_beat.disconnect()
    #     return wish_list


hyd_sys = HydSystem()


