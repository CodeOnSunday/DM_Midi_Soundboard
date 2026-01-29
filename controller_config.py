"""A module to handle the midi device configuration file."""
from pydantic import BaseModel
import json
import yaml
import sys
import pathlib

class ControllerEndpoint(BaseModel):
    """A midi event with a id code."""
    id_code: int

class ControllerKey(ControllerEndpoint):
    """A midi key with a position in a xy grid."""
    x: int
    y: int

class ControllerChannel(ControllerEndpoint):
    """A midi control channel with a position related to a group of keys."""
    x: int

class MidiDevice(BaseModel):
    """The midi device ids for input and output."""
    input_id: int
    output_id: int

class ControllerConfig(BaseModel):
    """The combination of all needed information to describe the midi device."""
    keys: list[ControllerKey]
    channels: list[ControllerChannel]
    master_channel: ControllerEndpoint
    master_stop: ControllerEndpoint
    device: MidiDevice


def get_controller_config() -> ControllerConfig:
    """Open and return the default controller configuration yaml file."""
    config_file = pathlib.Path("controller_config.yaml")
    if hasattr(sys, "_MEIPASS"):
        config_file = pathlib.Path(sys._MEIPASS) / config_file
        
    with open(config_file, "r") as ifile:
        return ControllerConfig(
            **yaml.load(ifile, Loader=yaml.FullLoader)
        )

if __name__ == "__main__":
    # generate the schema file
    with open("controller_config_schema.json", "w") as ofile:
        json.dump(
            ControllerConfig.model_json_schema(),
            ofile,
            indent=2
        )
            