"""
APEXPROBE | Virtual WIPS Tab (V11 "Golden Goose" Logic)
------------------------------------------------------
Scope: 
UI Layout preserved. Logic driven by lib/codes.py.
Tabs page handles UI building and argument collection only.
Housings for PNG cycle diagrams are managed here.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from lib import codes as NC
import os

# Pillow is required for handling PNG/JPG diagrams in Tkinter
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("CRITICAL: Pillow library not found. Run 'pip install Pillow' in your terminal.")


# --- IMAGE MAPPING ---
# This is the "Source of Truth" for visual cycle identification
CYCLE_IMAGES = {
    "A10 - Bore (Internal)": "bore.png",
    "A11 - Boss (External)": "boss.png",
    "A12 - Rectangular Pocket": "rect_pocket.png", 
    "A13 - Rectangular Boss": "rect_boss.png",
    "A14 - Web X": "web_x.png",
    "A15 - Pocket X": "pocket_x.png",
    "A16 - Web Y": "web_y.png",
    "A17 - Pocket Y": "pocket_y.png",
    "A20 - Surface Z": "surf_z.png",
    "A20 - Surface X": "surf_x.png",
    "A20 - Surface Y": "surf_y.png"
}

class WIPSTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # --- Persistent State (UI Variables) ---
        self.tool_var = tk.StringVar(value="50")
        self.work_var = tk.StringVar(value="54")
        self.is_ext_var = tk.BooleanVar(value=False)
        self.post_header_var = tk.BooleanVar(value=False) 
        
        # Position Parameters (X/Y Start)
        self.x_pos = tk.StringVar(value="0.0")
        self.y_pos = tk.StringVar(value="0.0")

        # Probing Depth/Heights
        self.probing_plane_z = tk.StringVar(value="0.1")
        self.clear_z = tk.StringVar(value="1.0")
        self.prot_z = tk.StringVar(value="0.5")
        
        # Cycle Selection
        self.cycle_var = tk.StringVar(value="A10 - Bore (Internal)")
        
        # G65 Arguments (D, E, H)
        self.d_var = tk.StringVar(value="1.0")    
        self.e_var = tk.StringVar(value="1.0")    
        self.h_var = tk.StringVar(value="-0.5")   
        
        # UI Helpers
        self.helper_text = tk.StringVar()
        self.widgets = {}
        self.img_label = None 

        self._build_ui()
        
        # Trace changes to sync UI behavior and Visuals
        self.cycle_var.trace_add("write", self._sync_all)
        self._sync_all()

    def _sync_all(self, *args):
        """Orchestrates UI updates and image swapping."""
        self._sync_v11_logic()
        self._update_image()

    def _sync_v11_logic(self, *args):
        """
        Syncs UI states with the metadata provided by the 'Brain'.
        Ensures unused variables are set to 0 while keeping inputs enabled.
        """
        if not self.widgets: return
            
        selection = self.cycle_var.get()
        
        # Fetch metadata (Help text, defaults, and usage states) from lib/codes.py
        help_msg, defaults, states = NC.get_cycle_metadata(selection)
        
        # Update Helper text
        self.helper_text.set(help_msg)

        # Sync variables with Brain's defaults (e.g. resets unused args to "0")
        self.d_var.set(defaults.get("d", "0"))
        self.e_var.set(defaults.get("e", "0"))
        self.h_var.set(defaults.get("h", "0"))

        # In V11 "Golden Goose" logic, we keep all fields enabled
        for widget in self.widgets.values():
            widget.configure(state="normal")

    def _update_image(self):
        """Resolves and loads the cycle diagram from the assets folder."""
        if not self.img_label: return

        if not PILLOW_AVAILABLE:
            self.img_label.configure(text="Pillow library missing.\nRun: pip install Pillow", image="")
            return

        selection = self.cycle_var.get()
        img_name = CYCLE_IMAGES.get(selection, "placeholder.png")
        
        # Find path to assets relative to this file
        search_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", img_name),
            os.path.join(os.getcwd(), "assets", img_name)
        ]

        img_path = None
        for path in search_paths:
            if os.path.exists(path):
                img_path = path
                break

        try:
            target_w, target_h = 350, 250
            if img_path:
                pill_img = Image.open(img_path)
                pill_img = pill_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(pill_img)
                self.img_label.configure(image=tk_img, text="")
                self.img_label.image = tk_img 
            else:
                self.img_label.configure(image="", text=f"[ Image Missing ]\nFilename: {img_name}")
        except Exception:
            self.img_label.configure(text="Error loading image asset", image="")

    def _build_ui(self):
        # --- LEFT PANEL: SETTINGS ---
        ctrl = ttk.LabelFrame(self, text=" WIPS-V11 Engine ", padding=15)
        ctrl.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

        # 1. Machine & Position Setup
        setup_f = ttk.Frame(ctrl)
        setup_f.pack(fill="x")
        
        # Tool and Work Offset
        ttk.Label(setup_f, text="Tool #:").grid(row=0, column=0, sticky="w")
        ttk.Entry(setup_f, textvariable=self.tool_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        ttk.Label(setup_f, text="Work:").grid(row=1, column=0, sticky="w")
        ttk.Entry(setup_f, textvariable=self.work_var, width=10).grid(row=1, column=1, padx=5, pady=2)
        ttk.Checkbutton(setup_f, text="Ext P1-99", variable=self.is_ext_var).grid(row=1, column=2, padx=10)
        ttk.Checkbutton(setup_f, text="Post % / O-Num", variable=self.post_header_var).grid(row=0, column=2, padx=10)

        # Start Position (X/Y)
        ttk.Label(setup_f, text="X Start:").grid(row=2, column=0, sticky="w")
        ttk.Entry(setup_f, textvariable=self.x_pos, width=10).grid(row=2, column=1, padx=5, pady=2)
        ttk.Label(setup_f, text="Y Start:").grid(row=2, column=2, sticky="w")
        ttk.Entry(setup_f, textvariable=self.y_pos, width=10).grid(row=2, column=3, padx=5, pady=2)

        ttk.Separator(ctrl, orient="horizontal").pack(fill="x", pady=10)

        # 2. Cycle Selection
        ttk.Label(ctrl, text="Select Probing Cycle:").pack(anchor="w")
        cycle_options = sorted(list(CYCLE_IMAGES.keys()))
        cb = ttk.Combobox(ctrl, textvariable=self.cycle_var, values=cycle_options, state="readonly", width=35)
        cb.pack(fill="x", pady=5)

        # 3. Visual Preview
        img_container = ttk.Frame(ctrl, width=360, height=270)
        img_container.pack(pady=10)
        img_container.pack_propagate(False) 
        
        img_frame = ttk.LabelFrame(img_container, text=" Cycle Diagram ", padding=5)
        img_frame.pack(fill="both", expand=True)
        
        self.img_label = tk.Label(img_frame, bg="#2c3e50", fg="white", width=350, height=250)
        self.img_label.pack(expand=True)

        # 4. G65 Arguments
        p_frame = ttk.LabelFrame(ctrl, text=" G65 Arguments ", padding=10)
        p_frame.pack(fill="x", pady=5)
        
        for i, (arg, var) in enumerate([("D", self.d_var), ("E", self.e_var), ("H", self.h_var)]):
            ttk.Label(p_frame, text=f"{arg} Argument:").grid(row=i, column=0, sticky="w")
            w = ttk.Entry(p_frame, textvariable=var, width=12)
            w.grid(row=i, column=1, padx=10, pady=2)
            self.widgets[arg.lower()] = w

        help_lbl = tk.Label(p_frame, textvariable=self.helper_text, font=("Segoe UI", 9, "italic"), 
                           fg="#3498db", wraplength=350, justify="left")
        help_lbl.grid(row=3, column=0, columnspan=2, pady=10, sticky="w")

        # 5. Safety Z Heights
        z_frame = ttk.LabelFrame(ctrl, text=" Safety Heights ", padding=10)
        z_frame.pack(fill="x", pady=5)
        ttk.Label(z_frame, text="Clearance:").grid(row=0, column=0, sticky="w")
        ttk.Entry(z_frame, textvariable=self.clear_z, width=10).grid(row=0, column=1, padx=10)
        ttk.Label(z_frame, text="Protected:").grid(row=1, column=0, sticky="w")
        ttk.Entry(z_frame, textvariable=self.prot_z, width=10).grid(row=1, column=1, padx=10)
        ttk.Label(z_frame, text="Probing Plane:").grid(row=2, column=0, sticky="w")
        ttk.Entry(z_frame, textvariable=self.probing_plane_z, width=10).grid(row=2, column=1, padx=10)

        # 6. Action Buttons
        btn_f = ttk.Frame(ctrl)
        btn_f.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_f, text="GENERATE G-CODE", command=self.generate).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(btn_f, text="COPY", command=self.copy_to_clip).pack(side="left", expand=True, fill="x", padx=5)

        # --- RIGHT PANEL: OUTPUT ---
        self.txt = tk.Text(self, font=("Consolas", 11), bg="#1e272e", fg="#d2dae2", 
                          padx=15, pady=15, relief="flat")
        self.txt.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

    def generate(self):
        try:
            selection = self.cycle_var.get()
            raw_key = selection.split("-")[0].strip()
            
            # Map sub-keys for surface cycles (A20 variants)
            cycle_key = raw_key
            if raw_key == "A20":
                if "Surface X" in selection: cycle_key = "A20X"
                elif "Surface Y" in selection: cycle_key = "A20Y"
                elif "Surface Z" in selection: cycle_key = "A20Z"

            # 1. Collect params through lib/codes.py collector
            params = NC.collect_user_params(
                t_num=self.tool_var.get(),
                wcs=self.work_var.get(),
                probe_cycle=cycle_key,
                z_clr=self.clear_z.get(),
                z_protect=self.prot_z.get(),
                probe_plane=self.probing_plane_z.get(),
                xpos=self.x_pos.get(),
                ypos=self.y_pos.get(),
                is_ext=self.is_ext_var.get(),
                args_dict={"D": self.d_var.get(), "E": self.e_var.get(), "H": self.h_var.get()}
            )

            # 2. Generate toolpath using the Brain engine
            prog = NC.generate_toolpath(params)
            
            # Add descriptive header
            prog.insert(0, f"(PROBE CYCLE: {selection})")

            # Handle Optional Post wrapping
            if self.post_header_var.get():
                prog.insert(0, "%")
                prog.insert(1, "O1001 (WIPS V11 APEXPROBE)")
                if prog[-1].strip() != "M01": prog.append("M01")
                prog.append("M30")
                prog.append("%")
            
            self.txt.delete("1.0", "end")
            self.txt.insert("end", "\n".join(prog))
            
        except Exception as e:
            messagebox.showerror("Generator Error", f"Invalid input parameters.\n{str(e)}")

    def copy_to_clip(self):
        self.txt.tag_add("sel", "1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(self.txt.get("1.0", "end"))