"""Support for Xiaomi binary sensors."""
import logging

from homeassistant.components.switch import SwitchDevice
from homeassistant.components.xiaomi import (PY_XIAOMI_GATEWAY, XiaomiDevice)

_LOGGER = logging.getLogger(__name__)

ATTR_LOAD_POWER = 'Load power'  # Load power in watts (W)
ATTR_POWER_CONSUMED = 'Power consumed'
ATTR_IN_USE = 'In use'
LOAD_POWER = 'load_power'
POWER_CONSUMED = 'power_consumed'
IN_USE = 'inuse'


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Perform the setup for Xiaomi devices."""
    devices = []
    for (_, gateway) in hass.data[PY_XIAOMI_GATEWAY].gateways.items():
        for device in gateway.devices['switch']:
            model = device['model']
            if model == 'plug':
                devices.append(XiaomiGenericSwitch(device, "Plug", 'status',
                                                   True, gateway))
            elif model == 'ctrl_neutral1':
                devices.append(XiaomiGenericSwitch(device, 'Wall Switch',
                                                   'channel_0',
                                                   False, gateway))
            elif model == 'ctrl_ln1':
                devices.append(XiaomiGenericSwitch(device, 'Wall Switch LN',
                                                   'channel_0',
                                                   False, gateway))
            elif model == 'ctrl_neutral2':
                devices.append(XiaomiGenericSwitch(device, 'Wall Switch Left',
                                                   'channel_0',
                                                   False, gateway))
                devices.append(XiaomiGenericSwitch(device, 'Wall Switch Right',
                                                   'channel_1',
                                                   False, gateway))
            elif model == 'ctrl_ln2':
                devices.append(XiaomiGenericSwitch(device,
                                                   'Wall Switch LN Left',
                                                   'channel_0',
                                                   False, gateway))
                devices.append(XiaomiGenericSwitch(device,
                                                   'Wall Switch LN Right',
                                                   'channel_1',
                                                   False, gateway))
            elif model == '86plug':
                devices.append(XiaomiGenericSwitch(device, 'Wall Plug',
                                                   'status', True, gateway))
    add_devices(devices)


class XiaomiGenericSwitch(XiaomiDevice, SwitchDevice):
    """Representation of a XiaomiPlug."""

    def __init__(self, device, name, data_key, supports_power_consumption,
                 xiaomi_hub):
        """Initialize the XiaomiPlug."""
        self._data_key = data_key
        self._in_use = None
        self._load_power = None
        self._power_consumed = None
        self._supports_power_consumption = supports_power_consumption
        XiaomiDevice.__init__(self, device, name, xiaomi_hub)

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        if self._data_key == 'status':
            return 'mdi:power-plug'
        return 'mdi:power-socket'

    @property
    def is_on(self):
        """Return true if it is on."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        if self._supports_power_consumption:
            attrs = {ATTR_IN_USE: self._in_use,
                     ATTR_LOAD_POWER: self._load_power,
                     ATTR_POWER_CONSUMED: self._power_consumed}
        else:
            attrs = {}
        attrs.update(super().device_state_attributes)
        return attrs

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        if self._write_to_hub(self._sid, **{self._data_key: 'on'}):
            self._state = True
            self.schedule_update_ha_state()

    def turn_off(self):
        """Turn the switch off."""
        if self._write_to_hub(self._sid, **{self._data_key: 'off'}):
            self._state = False
            self.schedule_update_ha_state()

    def parse_data(self, data):
        """Parse data sent by gateway."""
        if IN_USE in data:
            self._in_use = int(data[IN_USE])
            if not self._in_use:
                self._load_power = 0
        if POWER_CONSUMED in data:
            self._power_consumed = round(float(data[POWER_CONSUMED]), 2)
        if LOAD_POWER in data:
            self._load_power = round(float(data[LOAD_POWER]), 2)

        value = data.get(self._data_key)
        if value is None:
            return False

        state = value == 'on'
        if self._state == state:
            return False
        self._state = state
        return True
