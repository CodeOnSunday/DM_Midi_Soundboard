"""A script to generate the controller config yaml file, suitable for the AKAI APC mini midi controller."""

import yaml
from controller_config import ControllerChannel, ControllerEndpoint, ControllerConfig, ControllerKey, MidiDevice

if __name__ == "__main__":
    keys = [
        ControllerKey(id_code=id, x=id % 8, y=id // 8)
        for id in range(8*8)
    ]
    channels = [
        ControllerChannel(id_code=48 + id, x=id)
        for id in range(8)
    ]
    conf = ControllerConfig(
        keys=keys,
        channels=channels,
        master_channel=ControllerEndpoint(id_code=56),
        master_stop=ControllerEndpoint(id_code=119),
        device=MidiDevice(input_id=1, output_id=4)
    )
    with open("controller_config.yaml", "w") as ofile:
        ofile.write("""# yaml-language-server: $schema=controller_config_schema.json

""")
        yaml.dump(
            conf.model_dump(mode="json"),
            ofile,
            indent=2
        )
