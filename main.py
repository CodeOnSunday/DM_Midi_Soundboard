"""The main entry point to the tool which combines all the different modules."""
from asyncio import run, get_event_loop, sleep, create_task, wait, FIRST_COMPLETED
from functools import partial

import controller_config
import sound_config
from controller_manager import ControllerManager, Controller_SetVolume, Controller_KeyHit, Controller_MasterStop, Controller_MasterVolume, Controller_SetState
from sound_manager import SoundManager, SoundEntryManager
from ui_manager import run_ui, ask_for_soundboard_filename, show_notification

if __name__ == "__main__":
    async def loop():
        filename = ask_for_soundboard_filename()
        if len(filename) == 0:
            sc = sound_config.SoundConfig()
        else:
            sc = sound_config.get_sound_config(filename)
        
        sm = SoundManager(sc)

        cc = controller_config.get_controller_config()
        cm = ControllerManager(cc)

        match cm.is_device_opened_successfully():
            case [False, _]:
                show_notification("Can't open midi device for input and output.")
            case [True, False]:
                show_notification("Can't open midi device for output. Colored keys are not available.")

        def config_changed_handler():
            sm.reload_changed_config()

        config_changed_handler_call_func = partial(
            get_event_loop().call_soon_threadsafe,
            config_changed_handler
        )

        ui_thread = run_ui(
            sc, 
            dimensions=[8, 8], 
            handler=config_changed_handler_call_func,
            get_disabled_buttons=sm.get_xy_for_disabled_channels
        )

        async def ui_waiter():
            while ui_thread.is_alive():
                await sleep(0.5)
            

        async def ticker():
            while True:
                sm.tick()
                await sleep(0.1)

        def midi_handler(event):
            match event:
                case Controller_KeyHit(x, y):
                    sm.hit_note(x, y)
                case Controller_MasterStop():
                    sm.stop()
                case Controller_SetVolume(x, v_int):
                    sm.set_volume(x, v_int / 127.0)
                case Controller_MasterVolume(v_int):
                    sm.set_master_volume(v_int / 127.0)
        cm.set_event_handler(midi_handler)
        
        def sound_handler(sound: SoundEntryManager):
            x, y = sound.get_xy()
            state = sound.get_state()
            cm.set_state(
                Controller_SetState(x, y, state)
            )
        sm.set_change_handler(sound_handler)

        try:
            ticker_task = create_task(ticker())
            listener_task = create_task(cm.listen())
            ui_task = create_task(ui_waiter())
            await wait([ticker_task, listener_task, ui_task], return_when=FIRST_COMPLETED)
        except KeyboardInterrupt:
            pass

    run(loop())