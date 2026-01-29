"""This module just loads and dumps an config file to fill out any default fields and to check is the file is formatted correctly."""

import sound_config
import sys
import yaml

if __name__ == "__main__":
    config_filepath = sys.argv[1]
    SC = sound_config.get_sound_config(config_filepath)

    with open(config_filepath, "w") as ofile:
        ofile.write("""# yaml-language-server: $schema=sound_config_schema.json

""")
        yaml.dump(
            SC.model_dump(mode='json'),
            ofile,
            indent=2
        )