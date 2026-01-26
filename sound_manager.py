import sound_config
from pygame import mixer
from random import randint
from dataclasses import dataclass

mixer.init()

@dataclass
class SoundState:
    playing: bool
    paused: bool
    mode: sound_config.SoundPlayMode

class SoundEntryManager:
    def __init__(self, config_ref: sound_config.SoundEntry):
        self.config_ref = config_ref
        self.sound_obj = [
            mixer.Sound(path)
            for path in self.config_ref.files
        ]
        self.playing_channels: list[mixer.Channel]  = []
        self.playing_channel_paused: bool = False
        self.sound_obj_play_idx: int = len(self.sound_obj) - 1

    def is_at_position(self, x: int, y: int) -> bool:
        if x == self.config_ref.x and y == self.config_ref.y:
            return True
        return False
    
    def hit(self):
        match self.config_ref.mode:
            case sound_config.SoundPlayMode.PLAY:
                self.play_sound()
            case sound_config.SoundPlayMode.PLAY_AND_PAUSE:
                if self.is_playing():
                    self.toggle_pause()
                else:
                    self.play_sound()
            case sound_config.SoundPlayMode.PLAY_AND_STOP:
                if self.is_playing():
                    self.stop()
                else:
                    self.play_sound()

    def get_next_sound_obj(self) -> mixer.Sound:
        match self.config_ref.file_select:
            case sound_config.SoundFileSelect.SEQUENCE:
                self.sound_obj_play_idx = (self.sound_obj_play_idx + 1) % len(self.sound_obj)
            case sound_config.SoundFileSelect.RANDOM:
                self.sound_obj_play_idx = randint(0, len(self.sound_obj)-1)
        return self.sound_obj[self.sound_obj_play_idx]

    def set_volume(self, volume: float):
        for so in self.sound_obj:
            so.set_volume(volume)

    def is_playing(self):
        return len(self.playing_channels) > 0
    
    def is_paused(self):
        return self.playing_channel_paused

    def tick(self):
        if not self.is_playing():
            return
        match self.config_ref.mode:
            case sound_config.SoundPlayMode.PLAY:
                self.playing_channels = list(filter(lambda c: c.get_busy(), self.playing_channels))
                if not self.is_playing():
                    return True
            case sound_config.SoundPlayMode.PLAY_AND_PAUSE:
                if not self.is_paused():
                    if not self.playing_channels[0].get_busy():
                        self.play_sound()
            case sound_config.SoundPlayMode.PLAY_AND_STOP:
                if not self.playing_channels[0].get_busy():
                    self.play_sound()
        return False

    def play_sound(self):
        sound = self.get_next_sound_obj()
        if self.config_ref.mode in [sound_config.SoundPlayMode.PLAY_AND_PAUSE, sound_config.SoundPlayMode.PLAY_AND_STOP]:
            self.stop()
        self.playing_channels.append(sound.play())
        self.playing_channel_paused = False

    def stop(self):
        for channel in self.playing_channels:
            channel.fadeout(200)
        self.playing_channels.clear()

    def pause(self):
        for channel in self.playing_channels:
            channel.pause()
        self.playing_channel_paused = True

    def unpause(self):
        for channel in self.playing_channels:
            channel.unpause()
        self.playing_channel_paused = False

    def toggle_pause(self):
        if self.playing_channel_paused:
            self.unpause()
        else:
            self.pause()

    def get_state(self) -> SoundState:
        return SoundState(
            playing=self.is_playing(),
            paused=self.is_paused(),
            mode=self.config_ref.mode
        )
    
    def get_xy(self) -> tuple[int, int]:
        return self.config_ref.x, self.config_ref.y


class SoundManager:
    def __init__(self, config_ref: sound_config.SoundConfig):
        self.config_ref = config_ref
        self.sounds: dict[int, dict[int, SoundEntryManager]] = {}
        self.volumes: dict[int, float] = {}
        self.master_volume = 1.0

        self.reload_changed_config()

        self.change_handler = None

    def reload_changed_config(self):
        for sound in self.iterate_sounds():
            sound.stop()

        def get_x(x: int) -> dict[int, SoundEntryManager]:
            if x not in self.sounds:
                self.sounds[x] = {}
                self.volumes[x] = 1.0
            return self.sounds[x]
        for sound_conf in self.config_ref.sounds:
            sem = SoundEntryManager(sound_conf)
            x, y = sem.get_xy()
            get_x(x)[y] = sem

    def set_change_handler(self, handler):
        self.change_handler = handler

    def _call_handler(self, sound: SoundEntryManager):
        if self.change_handler is not None:
            self.change_handler(sound)

    def hit_note(self, x, y):
        try:
            sound = self.sounds[x][y]
            sound.hit()
            self._call_handler(sound)
        except KeyError:
            pass

    def iterate_sounds(self):
        for col in self.sounds.values():
            for sound in col.values():
                yield sound

    def tick(self):
       for sound in self.iterate_sounds():
           if sound.tick():
               self._call_handler(sound)

    def stop(self):
        for sound in self.iterate_sounds():
            sound.stop()
            self._call_handler(sound)

    def get_state(self) -> dict[int, dict[int, SoundState]]:
        result = {}
        for x in self.sounds:
            result[x] = {}
            for y in self.sounds[x]:
                result[x][y] = self.sounds[x][y].get_state()
        return result
    
    def set_volume(self, x: int, volume: float | None = None):
        try:
            if volume is not None:
                self.volumes[x] = volume
            for sound in self.sounds[x].values():
                sound.set_volume(self.volumes[x] * self.master_volume)
        except KeyError:
            pass

    def set_master_volume(self, volume: float):
        self.master_volume = volume
        for x in self.volumes:
            self.set_volume(x)
