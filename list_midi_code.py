"""A script to list the available midi devices and print the midi events send."""
from pygame import midi

midi.init()

print("Overview of midi devices:")
for i in range(midi.get_count()):
    info = midi.get_device_info(i)
    print(i, info)

print(f"Open default midi device ({midi.get_default_input_id()})")
device = midi.Input(midi.get_default_input_id())
try:
    while True:
        evt_lst = device.read(1)
        for evt_entry in evt_lst:
            data, ts = evt_entry
            st, d1, d2, d3 = data
            code = (st & 0xF0) >> 4
            match code:
                case 0x9:
                    print(f"Note On -- Key: {d1}")
                case 0x8:
                    print(f"Note Off -- Key: {d1}")
                case 0xB:
                    print(f"Control -- Key: {d1} Data: {d2}")
except KeyboardInterrupt:
    pass

midi.quit()