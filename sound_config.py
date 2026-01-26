from pydantic import BaseModel
import yaml
import json
import enum

class SoundPlayMode(str, enum.Enum):
    PLAY = 'play_and_layer'
    PLAY_AND_PAUSE = 'play_and_pause'
    PLAY_AND_STOP = 'play_and_stop'

class SoundFileSelect(str, enum.Enum):
    SEQUENCE = 'sequence'
    RANDOM = 'random'

class SoundEntry(BaseModel):
    text: str
    x: int
    y: int
    files: list[str]
    file_select: SoundFileSelect = SoundFileSelect.SEQUENCE
    mode: SoundPlayMode = SoundPlayMode.PLAY

class SoundConfig(BaseModel):
    sounds: list[SoundEntry] = []

def get_sound_config(path: str):
    with open(path, "r") as ifile:
        return SoundConfig(
            **yaml.load(ifile, Loader=yaml.FullLoader)
        )
    
if __name__ == "__main__":
    with open("sound_config_schema.json", "w") as ofile:
        json.dump(
            SoundConfig.model_json_schema(),
            ofile,
            indent=2
        )
    
    se = SoundEntry(
        text="A",
        x=0,y=0,
        files=[],
        mode=SoundPlayMode.PLAY,
        file_select=SoundFileSelect.SEQUENCE
    )
    print(se)
    print(type(se))
    se.mode = SoundPlayMode("play_and_layer")
    print(se)
    print(type(se))