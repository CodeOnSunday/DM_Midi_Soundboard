"""A module to communicate with the midi device."""

import controller_config
import asyncio
from pygame import midi
from dataclasses import dataclass
from sound_manager import SoundState
from sound_config import SoundPlayMode

midi.init()

@dataclass
class Controller_KeyHit:
    """Represents an key hit event at position xy."""
    x: int
    y: int

@dataclass
class Controller_MasterStop:
    """Represents that the global stop key is hit."""
    pass

@dataclass
class Controller_SetVolume:
    """Represents that a control channel associated with a column of keys got a new value."""
    x: int
    data: int

@dataclass
class Controller_MasterVolume:
    """Represents that the master volume channel got a new value."""
    data: int

@dataclass
class Controller_SetState:
    """Represents that the midi controller should represent a new sound state at position xy."""
    x: int
    y: int
    state: SoundState

class ControllerManager:
    """A class to communicate with the midi device."""

    def __init__(self, config_ref: controller_config.ControllerConfig):
        """
        Initialize the class and open the midi device.
        
        Args:
            config_ref(controller_config.ControllerConfig): The controller configuration.

        """
        self.config_ref = config_ref

        self.keys: dict[int, object] = {}
        for key in self.config_ref.keys:
            self.keys[key.id_code] = key

        self.channels: dict[int, object] = {}
        for channel in self.config_ref.channels:
            self.channels[channel.id_code] = channel

        self.master_channel = self.config_ref.master_channel
        self.master_stop = self.config_ref.master_stop

        try:
            self.input_device = midi.Input(self.config_ref.device.input_id)
            self.output_device = midi.Output(self.config_ref.device.output_id)
        except Exception:
            self.input_device = None
            self.output_device = None

        self.event_handler = None

    def is_device_opened_successfully(self) -> tuple[bool, bool]:
        """
        Returns True or False for the input and output device, if they are opened successfully.
        """
        return self.input_device is not None, self.output_device is not None

    def set_event_handler(self, handler = None):
        """
        Set the event handler to call for new events.

        Args:
            handler: A callable which is called with an object of the event type.
        
        """
        self.event_handler = handler

    def _call_event(self, data: object):
        """
        Call the event handler if set.
        
        Args:
            data: The arguments to pass to the handler.

        """
        if self.event_handler is not None:
            self.event_handler(data)
        
    async def listen(self):
        """
        The midi event process function to be called asynchronous.
        """
        if self.input_device is None:
            while True:
                await asyncio.sleep(1)
        while True:
            evt_lst = self.input_device.read(300)
            for evt_entry in evt_lst:
                data, _ = evt_entry
                st, d1, d2, _ = data
                code = (st & 0xF0) >> 4
                try:
                    match code:
                        case 0x9:
                            # Key On
                            if self.check_for_master_stop(d1):
                                self._call_event(Controller_MasterStop())
                            else:
                                x,y = self.get_xy_for_key(d1)
                                self._call_event(Controller_KeyHit(x, y))
                        case 0x8:
                            pass # Key Off currently not used
                        case 0xB:
                            # Control
                            if self.check_for_master_volume(d1):
                                self._call_event(Controller_MasterVolume(d2))
                            else:
                                x = self.get_x_for_channel(d1)
                                self._call_event(Controller_SetVolume(x, d2))
                except KeyError:
                    pass
            await asyncio.sleep(0.1)

    def check_for_master_stop(self, id: int) -> bool:
        """
        Check if the key code is identical to the configured master stop key code.
        """
        return self.master_stop.id_code == id
    
    def check_for_master_volume(self, id: int) -> bool:
        """
        Check if the control code is identical to the configured master volume control code.
        """
        return self.master_channel.id_code == id

    def get_xy_for_key(self, id: int) -> tuple[int, int]:
        """
        Returns the x and y coordinates for a key code. Raises an KeyError if the key code is not configured.
        """
        entry = self.keys[id]
        return entry.x, entry.y
        
    def get_key_for_xy(self, x: int, y: int) -> controller_config.ControllerKey:
        """
        Returns the key entry for the given x and y coordinates. Returns None if the coordinates don't match any key entry.
        """
        for key in self.keys.values():
            if key.x == x and key.y == y:
                return key
        
    def get_x_for_channel(self, id: int) -> int:
        """
        Returns the x coordinate for a control code. Raises an KeyError if the control code is not configured.
        """
        return self.channels[id].x
        
    def set_state(self, state: Controller_SetState):
        """
        Sends a command to the midi device to color a key at a position according to the sound mode and state.
        """
        if self.output_device is None:
            return
        
        try:
            pad_id = self.get_key_for_xy(state.x, state.y).id_code
            
            match state.state.mode:
                case SoundPlayMode.PLAY:
                    color = 5 # #FF0000
                case SoundPlayMode.PLAY_AND_PAUSE:
                    color = 45 # #0000FF
                case SoundPlayMode.PLAY_AND_STOP:
                    color = 21 # #00FF00

            cmd = 0x94
            if state.state.paused:
                cmd = 0x90
            if not state.state.playing:
                color = 0x00

            self.output_device.write_short(cmd, pad_id, color)
        except KeyError:
            pass