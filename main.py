"""The main entry point to the tool which combines all the different modules."""
from asyncio import run, get_event_loop, sleep, create_task, wait, FIRST_COMPLETED

import controller_config
import sound_config
from controller_manager import ControllerManager, Controller_SetVolume, Controller_KeyHit, Controller_MasterStop, Controller_MasterVolume, Controller_SetState, get_midi_device_list
from sound_manager import SoundManager, SoundEntryManager
from ui_manager import run_ui, UiManagerRequests, create_async_request_handler

if __name__ == "__main__":
    async def loop():
        sc = sound_config.SoundConfig()
        sm = SoundManager(sc)

        cc = controller_config.get_controller_config()
        cm = ControllerManager(cc)

        def request_handler(request: UiManagerRequests, *args):
            match request:
                case UiManagerRequests.GET_SOUND_ERROR_POSITIONS:
                    return sm.get_xy_for_disabled_sounds()
                case UiManagerRequests.RELOAD_AFTER_CONFIG_CHANGE:
                    sm.reload_changed_config()
                case UiManagerRequests.GET_MIDI_DEVICES:
                    return get_midi_device_list()
                case UiManagerRequests.GET_DEVICE_OPEN_STATE:
                    return cm.is_device_opened_successfully()
                
        ui_thread = run_ui(
            sc, 
            dimensions=[8, 8], 
            request_handler=create_async_request_handler(get_event_loop(), request_handler),
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