import sound_config

import tkinter as tk
from tkinter import ttk
from tkinter.messagebox import showwarning
from tkinter.filedialog import asksaveasfilename, askopenfilename
from tkinterdnd2 import DND_FILES, TkinterDnD
import threading
from functools import partial
import pathlib
from typing import Callable
import yaml
import jinja2

class UiEntryManager:
    def __init__(self, parent, config_ref: sound_config.SoundEntry):
        self.top = tk.Toplevel(parent)
        self.top.title("Edit Entry")
        self.top.transient(parent)
        self.top.grab_set()

        self.result = "UNCHANGED"

        grid_args = {
            "sticky": tk.NSEW,
            "padx": 5,
            "pady": 7
        }

        frame = tk.Frame(self.top)
        frame.pack(fill="both", expand=True)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(3, weight=1)


        text_label = tk.Label(frame, text="Text:")
        text_label.grid(column=0, row=0, **grid_args)

        text_entry = tk.Entry(frame)
        text_entry.insert(0, config_ref.text)
        text_entry.grid(column=1, row=0, **grid_args)


        mode_label = tk.Label(frame, text="Mode:")
        mode_label.grid(column=0, row=1, **grid_args)

        mode_string = tk.StringVar()
        mode_select = ttk.Combobox(frame, textvariable=mode_string)
        mode_options = [e.value for e in sound_config.SoundPlayMode]
        mode_select['values'] = mode_options
        mode_select['state'] = 'readonly'
        mode_select.current(mode_options.index(config_ref.mode.value))
        mode_select.grid(column=1, row=1, **grid_args)


        sequence_label = tk.Label(frame, text="Sequence:")
        sequence_label.grid(column=0, row=2, **grid_args)

        sequence_string = tk.StringVar()
        sequence_select = ttk.Combobox(frame, textvariable=sequence_string)
        sequence_options = [e.value for e in sound_config.SoundFileSelect]
        sequence_select['values'] = sequence_options
        sequence_select['state'] = 'readonly'
        sequence_select.current(sequence_options.index(config_ref.file_select.value))
        sequence_select.grid(column=1, row=2, **grid_args)
        

        files_label = tk.Label(frame, text="Files:")
        files_label.grid(column=0, row=3, **grid_args)

        files_listbox = tk.Listbox(frame, selectmode=tk.EXTENDED)
        for file in config_ref.files:
            files_listbox.insert(tk.END, file)

        def delete_handler(*args):
            selected_entries = files_listbox.curselection()
            for idx in sorted(selected_entries, reverse=True):
                files_listbox.delete(idx)

        def move_handler(move_up: bool = True, *args):
            selected_entries = files_listbox.curselection()
            selection_groups = []
            last_entry_selected = None
            for idx, file in enumerate(files_listbox.get(0, tk.END)):
                is_selected = idx in selected_entries
                if not is_selected or is_selected != last_entry_selected:
                    group_idx =  len(selection_groups)
                    if is_selected:
                        group_idx += -1.5 if move_up else 1.5
                    selection_groups.append([group_idx, is_selected])
                    last_entry_selected = is_selected
                selection_groups[-1].append(file)
            selection_groups = sorted(selection_groups, key=lambda e: e[0])
            files_listbox.delete(0, tk.END)
            for group in selection_groups:
                for file in group[2:]:
                    files_listbox.insert(tk.END, file)
                    if group[1]:
                        files_listbox.selection_set(tk.END)
            return "break"
        
        def drop_handler(event):
            files = self.top.tk.splitlist(event.data)
            paths = [pathlib.Path(file) for file in files]
            ref_path = pathlib.Path(__file__).parent
            def try_to_rel(path: pathlib.Path) -> pathlib.Path:
                try:
                    return path.relative_to(ref_path, walk_up=True)
                except ValueError:
                    return path
            rel_paths = [ try_to_rel(path) for path in paths]
            for path in rel_paths:
                files_listbox.insert(tk.END, str(path))

        files_listbox.bind("<Delete>", delete_handler)
        files_listbox.bind("<Up>", partial(move_handler, True))
        files_listbox.bind("<Down>", partial(move_handler, False))
        files_listbox.drop_target_register(DND_FILES)
        files_listbox.dnd_bind("<<Drop>>", drop_handler)
        files_listbox.grid(column=1, row=3, **grid_args)


        def del_close_handler(*args):
            self.result = None
            self.top.destroy()
            self.top = None

        del_btn = tk.Button(frame, text="Delete & Close", command=del_close_handler)
        del_btn.grid(column=0, row=4, **grid_args)
        
        def save_close_handler():
            files=list(
                files_listbox.get(0, tk.END)
            )

            sequence = sound_config.SoundFileSelect(sequence_string.get())
            mode = sound_config.SoundPlayMode(mode_string.get())
            self.result = config_ref
            self.result.text = text_entry.get()
            self.result.file_select=sequence
            self.result.mode=mode
            self.result.files=files

            self.top.destroy()
            self.top = None

        save_btn = tk.Button(frame, text="Save & Close", command=save_close_handler)
        save_btn.grid(column=1, row=4, **grid_args)

        # Center above parent
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        self.top.update_idletasks()
        dw = self.top.winfo_width()
        dh = self.top.winfo_height()

        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2

        self.top.geometry(f"+{x}+{y}")

    def __del__(self):
        if self.top is not None:
            self.top.destroy()

class UiManager:
    def __init__(self, parent, config_ref: sound_config.SoundConfig, dimensions: tuple[int, int], handler: Callable[[], None], get_disabled_buttons: Callable[[], list[tuple[int,int]]]):
        self.parent = parent

        self.config_ref = config_ref
        self.dim = dimensions
        self.changed_handler = handler
        self.get_disabled_buttons = get_disabled_buttons

        self.parent.title("GM Midi Soundboard")
        
        self.button_frame = tk.Frame(self.parent)
        self.button_frame.pack(fill="both", expand=True)
        self.button_frame.grid_columnconfigure(list(range(dimensions[0])), weight=1)
        self.button_frame.grid_rowconfigure(list(range(dimensions[1])), weight=1)

        self.save_btn = tk.Button(self.parent, text="Save", command=self.on_save_handler)
        self.save_btn.pack(padx=5, pady=7)

        self.reload_changed_config()
        self.parent.eval('tk::PlaceWindow . center')
        self.parent.attributes("-topmost", True)
        self.parent.attributes("-topmost", False)

        self.drag_btn = None

    def on_save_handler(self, *args):
        filename = asksaveasfilename(initialfile="Soundboard.yaml", defaultextension=".yaml", filetypes=[("Soundboard YAML", "*.yaml")])
        if len(filename) > 0:
            with open(filename, "w") as f:
                f.write("""# yaml-language-server: $schema=sound_config_schema.json

""")
                yaml.dump(
                    self.config_ref.model_dump(mode="json"),
                    f,
                    indent=2
                )
                f.close()

            env = jinja2.Environment(
                loader=jinja2.FileSystemLoader("."),
                autoescape=jinja2.select_autoescape(["html", "xml"])
            )
            template = env.get_template("overview.html.template")

            grid = [ [''] * self.dim[0] for _ in range(self.dim[1])]
            for se in self.config_ref.sounds:
                grid[self.dim[1] - 1 - se.y][se.x] = se.text

            html = template.render(rows=grid, width = 100.0 / self.dim[0])
            filepath = pathlib.Path(filename)
            with open(filepath.with_suffix(".html"), "w", encoding="utf-8") as f:
                f.write(html)

    def _call_changed_handler(self):
        self.reload_changed_config()
        if self.changed_handler is not None:
            self.changed_handler()

    def find_entry_for_xy(self, x: int, y: int) -> sound_config.SoundEntry | None:
        for sound in self.config_ref.sounds:
            if sound.x == x and sound.y == y:
                return sound
        return None

    def on_mouse_down(self, event):
        if isinstance(event.widget, tk.Button):
            self.drag_btn = event.widget

    def on_mouse_up(self, event):
        if isinstance(event.widget, tk.Button):
            target = event.widget.winfo_containing(event.x_root, event.y_root)
            if target != self.drag_btn:
                a_info = self.drag_btn.grid_info()
                a_xy = (a_info["column"], self.dim[1] - 1 - a_info["row"])
                b_info = target.grid_info()
                b_xy = (b_info["column"], self.dim[1] - 1 - b_info["row"])
                a = self.find_entry_for_xy(*a_xy)
                b = self.find_entry_for_xy(*b_xy)
                if a is not None:
                    a.x = b_xy[0]
                    a.y = b_xy[1]
                if b is not None:
                    b.x = a_xy[0]
                    b.y = a_xy[1]
                self._call_changed_handler()

    def reload_changed_config(self):
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        
        def open_dialog_for_entry(entry: sound_config.SoundEntry):
            diag = UiEntryManager(self.parent, entry)
            self.parent.wait_window(diag.top)
            match diag.result:
                case "UNCHANGED":
                    return
                case None:
                    idx = self.config_ref.sounds.index(entry)
                    del self.config_ref.sounds[idx]
                    self._call_changed_handler()
                case sound_config.SoundEntry():
                    self._call_changed_handler()
            del diag

        def open_dialog_for_new_entry(x: int, y: int):
            new_entry = sound_config.SoundEntry(
                text="New",
                x=x,
                y=y,
                files=[],
                file_select=sound_config.SoundFileSelect.SEQUENCE,
                mode=sound_config.SoundPlayMode.PLAY_AND_STOP
            )
            diag = UiEntryManager(self.parent, new_entry)
            self.parent.wait_window(diag.top)
            match diag.result:
                case "UNCHANGED" | None:
                    return
                case sound_config.SoundEntry():
                    self.config_ref.sounds.append(diag.result)
                    self._call_changed_handler()
            del diag

        disabled_buttons = self.get_disabled_buttons()
        
        for xi in range(self.dim[0]):
            for yi in range(self.dim[1]):
                se = self.find_entry_for_xy(xi, yi)
                kwargs = {
                    "text": se.text if se is not None else "-",
                }
                if (xi, yi) in disabled_buttons:
                    kwargs["bg"] = "lightgray"
                if se is None:
                    kwargs["command"] = partial(open_dialog_for_new_entry, xi, yi)
                else:
                    kwargs["command"] = partial(open_dialog_for_entry, se)
                btn = tk.Button(self.button_frame, **kwargs)
                btn.bind("<ButtonPress-1>", self.on_mouse_down)
                btn.bind("<ButtonRelease-1>", self.on_mouse_up)    
                btn.grid(column=xi, row=self.dim[1] - 1 - yi, sticky=tk.NSEW, padx=2, pady=2)

def run_ui(*args, **kwargs):
    def _run_ui(*args, **kwargs):
        root = TkinterDnD.Tk()
        ui = UiManager(root, *args, **kwargs)
        root.mainloop()
        del ui

    thread = threading.Thread(
        target=_run_ui,
        args=args,
        kwargs=kwargs,
        daemon=True
    )
    thread.start()
    return thread

def ask_for_soundboard_filename() -> str | None:
    return askopenfilename(filetypes=[("Soundboard YAML", "*.yaml")])

def show_notification(text): 
    showwarning("Warning", text)