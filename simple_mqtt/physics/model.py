class PressureNode:
    def __init__(self):
        """
        initialize a hydraulic node, which maintains data of pressure,
        """
        self._pressure = 1

    @property
    def pressure(self):
        return self._pressure
        pass

    @pressure.setter
    def pressure(self, value):
        self._pressure = value

    def bind(self):
        """bind the node to a pressure measurement IO"""
        pass


class Rotor:
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


class Motor()
    def __init__(self):
        self._rotor = Rotor()
        self._temperature = None

    @property
    def omega(self):
        return self._rotor.omega

    @omega.setter
    def omega(self, value):
        self._rotor.omega = value

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value):
        self._temperature = value



class Pump:
    def __init__(self):
        """
        initialize a hydraulic pump, which generate
        """
        self._intake = PressureNode()
        self._outlet = PressureNode()
        self._rotor = Rotor()
        self._displacement = 0
        
    @property
    def flow(self):
        return self._rotor.omega * self._displacement


class Source:
    def __init__(self):
        """
        Initialization of hydraulic power source. It includes information of tank, pump, and relevant circuits.
        """
        self.pump = Pump()
        self.intake = self.pump.intake
        self.outlet = self.pump.outlet
        pass
