import drv8837
import power_supply
import time
import collections

class MotorControl:

    '''
    High level control logic all aspects of the motor control.

    Provides the abilty to set the motor direction and voltage.
    Returns measured voltage, current, RPM, and temperature.

    Key requirements in addtion to the above functionality are:
    - PSU can only be enabled when set to 1V and motor is in brake mode.
    - PSU can only change voltage in 50mv steps at a rate of 50mV / ms to prevent the supply rail from crashing.
    - Motor can only transistion between forward and reverse by braking for a minmum amount of time first.
    - Motor can only be enabled or disabled when the PSU is set to 1V and in brake mode.

    Example:

        psu = PSU(i2c, en_pin=16, dac_addr=0x60, imon_addr=0x40)
        drv = DRV8837(motor_en=15, motor_in1=6, motor_in2=5)
        temp = TMP1075(i2c, addr=0x48)
        rpm = RPM(pin=14)

        motor = MotorControl(psu, drv, rpm, temp)

        motor.set_state(FORWARD, 1.0)
        motor.get_voltage()
        motor.get_current()
        motor.get_rpm()
        motor.get_temp()
        motor.set_state(REVERSE, 3.0)
    '''

    # States for the user to command
    MOTOR_BRAKE = 1
    MOTOR_FORWARD = 2
    MOTOR_REVERSE = 3

    VOLTAGE_MIN_MV = 1000
    VOLTAGE_MAX_MV = 3000

    def __init__(self, psu, drv, rpm, temp, brake_time: float = 1, ramp_rate: int = 50):
        self.psu = psu
        self.drv = drv
        self.rpm = rpm
        self.temp = temp
        # Soft start
        self.brake_time_ms = int(brake_time * 1000)
        self.ramp_rate = ramp_rate
        self.previous_ramp_time = time.ticks_ms()
        self.brake_start_time = None
        # Motor State
        self.motor_enabled = False
        self.motor_direction = self.MOTOR_BRAKE
        self.target_motor_direction = self.MOTOR_BRAKE
        # PSU State
        self.psu_enabled = False
        self.voltage_mv = self.VOLTAGE_MIN_MV
        self.target_voltage_mv = self.VOLTAGE_MIN_MV
        # Current Averaging
        self.current_samples_100ms = collections.deque((), 10)
        self.current_samples_1s = collections.deque((), 100)
        self.current_last_sample_time = time.ticks_ms()
        self.current_last_avg = (0.0, 0.0)
        # RPM Averaging

        # Set default states
        self.psu.disable()
        self.psu.set_voltage(self.voltage_mv / 1000)
        self.drv.brake()
        self.drv.enable() # We don't want to enable / disable the DRV during use, instead use brake to disable motion
        self.psu.enable() # Likewise, we'll leave the PSU on at all times and just use brake to disable motion

    def set_state(self, direction: int, voltage: float):
        '''
        Sets motor direction and voltage following the rules in the docstring
        '''

        # Bounds check voltage and set target
        if voltage < 1.0:
            self.target_voltage_mv = self.VOLTAGE_MIN_MV
            raise ValueError(f'Set Voltage {voltage}V is below minimum of 1.0V, setting to 1.0V')
        elif voltage > 3.0:
            self.target_voltage_mv = self.VOLTAGE_MAX_MV
            raise ValueError(f'Set Voltage {voltage}V is above maximum of 3.0V, setting to 3.0V')
        else:
            self.target_voltage_mv = int(voltage * 1000)
        
        # Sets target direction, this does not handle the logic of when we change, just the desired end state
        if direction not in [self.MOTOR_BRAKE, self.MOTOR_FORWARD, self.MOTOR_REVERSE]:
            raise ValueError(f'Invalid motor direction {direction}, must be 1 (brake), 2 (forward), or 3 (reverse)')
        else:
            self.target_motor_direction = direction
        
    def ramp_voltage(self, target_voltage_mv: float = None):
        if target_voltage_mv == None:
            target_voltage_mv = self.target_voltage_mv

        now = time.ticks_ms()

        # If it's been more than 1ms since the last voltage change, it's valid to do it again
        if time.ticks_diff(now, self.previous_ramp_time) > 1:
            # If we are more than 50mV away from the target voltage, adjust in 50mV steps
            if abs(target_voltage_mv - self.voltage_mv):
                if target_voltage_mv > self.voltage_mv:
                    self.voltage_mv = self.voltage_mv + 50
                elif target_voltage_mv < self.voltage_mv:
                    self.voltage_mv = self.voltage_mv - 50
                self.psu.set_voltage(self.voltage_mv / 1000)
                self._last_ramp_time = now

    def update_state(self):
        now = time.ticks_ms()

        # If we want to change direction and the motor is not in brake, we need to brake first for a set amount of time
        if self.target_motor_direction != self.motor_direction:
            # If we want to change direction and the set voltage is not 1V, we need to ramp down to 1V first
            if self.voltage_mv != self.VOLTAGE_MIN_MV:
                self.ramp_voltage(target_voltage_mv=self.VOLTAGE_MIN_MV)
            elif self.motor_direction != self.MOTOR_BRAKE:
                # We are currently moving and want to change direction, so brake and start timer
                self.drv.brake()
                self.brake_start_time = now
                self.motor_direction = self.MOTOR_BRAKE
            else:
                # If we are current braking and want to change direction, check if we've been braking long enough to change direction
                if time.ticks_diff(now, self.brake_start_time) > self.brake_time_ms:
                    # We've been braking long enough, change direction
                    if self.target_motor_direction == self.MOTOR_FORWARD:
                        self.drv.forward()
                    elif self.target_motor_direction == self.MOTOR_REVERSE:
                        self.drv.reverse()
                    self.motor_direction = self.target_motor_direction
        # If we are in the correct state but the voltage is not correct, ramp to the correct voltage
        elif self.voltage_mv != self.target_voltage_mv:
            self.ramp_voltage()

    def get_voltage(self):
        '''Get voltage from current sensor'''
        return self.psu.get_voltage()
    
    def update_current(self):
        '''
        This function will sample the current every 10ms and create rolling averages
        '''
        now = time.ticks_ms()
        if time.ticks_diff(now, self.current_last_sample_time) >= 10:
            current = self.psu.get_current(10) # This gets rid of the very high frequency noise
            self.current_samples_100ms.append(current)
            self.current_samples_1s.append(current)
            self.current_last_sample_time = now

            avg_100ms = sum(self.current_samples_100ms) / len(self.current_samples_100ms)
            avg_1s = sum(self.current_samples_1s) / len(self.current_samples_1s)
            self.current_last_avg = (avg_100ms, avg_1s)

    def get_current_100ms(self):
        return self.current_last_avg[0]
    
    def get_current_1s(self):
        return self.current_last_avg[1]
    
    def get_temp(self):
        ''''
        Returns raw temperature, no need to average as dTdt is slow and not very noisy
        '''
        return self.temp.get_temperature()