"""
APEXPROBE | Measure Features Tab
------------------------------------------------------------------
Scope:
Generates a sequence of Renishaw probing cycles with optional
program headers/wrappers. Logic delegated to lib/codes.py.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from lib import codes as NC

class MeasureFeaturesTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # --- State ---
        self.features = [] 
        
        # Cycle Specifications (Mapped to Brain keys)
        self.cycle_specs = {
            "A10 - Bore":        {"req": ["D"],           "key": "A10"},
            "A11 - Boss":        {"req": ["D", "H"],      "key": "A11"},
            "A12 - Rect Pocket": {"req": ["D", "E"],      "key": "A12"},
            "A13 - Rect Boss":   {"req": ["D", "E", "H"], "key": "A13"},
            "A14 - Web X":       {"req": ["D", "H"],      "key": "A14"},
            "A15 - Pocket X":    {"req": ["D"],           "key": "A15"},
            "A16 - Web Y":       {"req": ["E", "H"],      "key": "A16"},
            "A17 - Pocket Y":    {"req": ["E"],           "key": "A17"},
            "A20 - Surface X":   {"req": ["D"],           "key": "A20X"},
            "A20 - Surface Y":   {"req": ["E"],           "key": "A20Y"},
            "A20 - Surface Z":   {"req": ["H"],           "key": "A20Z"}
        }

        # Machine & Program Setup
        self.tool_var = tk.StringVar(value="50")
        self.work_var = tk.StringVar(value="54")
        self.is_ext_var = tk.BooleanVar(value=False)
        
        # Program Wrapping & Termination preferences
        self.post_header_var = tk.BooleanVar(value=False)
        self.program_num_var = tk.StringVar(value="1234")
        self.use_m99_var = tk.BooleanVar(value=False)
        
        # Global Heights
        self.clearance_z = tk.StringVar(value="6.0")
        self.protected_z = tk.StringVar(value="1.0")

        self._build_ui()
        self._add_feature()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        input_panel = ttk.Frame(self)
        input_panel.grid(row=0, column=0, sticky="nsw", padx=(20, 10), pady=10)

        # 1. Machine Setup
        setup_f = ttk.LabelFrame(input_panel, text=" Machine Setup ", padding=10)
        setup_f.pack(fill="x", pady=(0, 10))
        
        r1 = ttk.Frame(setup_f); r1.pack(fill="x", pady=2)
        ttk.Label(r1, text="Probe T#:").pack(side="left")
        ttk.Entry(r1, textvariable=self.tool_var, width=8).pack(side="left", padx=5)
        
        r2 = ttk.Frame(setup_f); r2.pack(fill="x", pady=2)
        ttk.Label(r2, text="WCS:").pack(side="left")
        ttk.Entry(r2, textvariable=self.work_var, width=8).pack(side="left", padx=5)
        ttk.Checkbutton(r2, text="Ext", variable=self.is_ext_var).pack(side="left")

        # Program Header & Termination Controls
        r3 = ttk.Frame(setup_f); r3.pack(fill="x", pady=2)
        ttk.Checkbutton(r3, text="Post % / O-Num", variable=self.post_header_var).pack(side="left")
        ttk.Label(r3, text=" O:").pack(side="left")
        ttk.Entry(r3, textvariable=self.program_num_var, width=6).pack(side="left", padx=2)

        r4 = ttk.Frame(setup_f); r4.pack(fill="x", pady=2)
        ttk.Checkbutton(r4, text="End with M99 (Sub-Prog)", variable=self.use_m99_var).pack(side="left")

        # 2. Global Heights
        h_f = ttk.LabelFrame(input_panel, text=" Global Heights ", padding=10)
        h_f.pack(fill="x", pady=(0, 10))
        ttk.Label(h_f, text="Clearance Z:").grid(row=0, column=0, sticky="w")
        ttk.Entry(h_f, textvariable=self.clearance_z, width=8).grid(row=0, column=1, padx=5)
        ttk.Label(h_f, text="Protect Z:").grid(row=1, column=0, sticky="w")
        ttk.Entry(h_f, textvariable=self.protected_z, width=8).grid(row=1, column=1, padx=5)

        # 3. Feature Sequence
        f_lab = ttk.LabelFrame(input_panel, text=" Probing Sequence ", padding=10)
        f_lab.pack(fill="both", expand=True)
        btn_f = ttk.Frame(f_lab); btn_f.pack(fill="x", pady=(0, 10))
        ttk.Button(btn_f, text="+ Add Feature", command=self._add_feature).pack(side="left", padx=2)
        ttk.Button(btn_f, text="Clear All", command=self._clear_features).pack(side="left", padx=2)
        
        self.canvas = tk.Canvas(f_lab, borderwidth=0, highlightthickness=0, width=500)
        self.scrollbar = ttk.Scrollbar(f_lab, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = ttk.Frame(self.canvas)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Output Panel (Right)
        output_panel = ttk.Frame(self)
        output_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=10)
        act_f = ttk.Frame(output_panel); act_f.pack(fill="x", pady=(0, 5))
        ttk.Button(act_f, text="GENERATE MEASUREMENTS", command=self._generate).pack(side="left", fill="x", expand=True)
        
        self.out = tk.Text(output_panel, font=("Consolas", 11), bg="#1e272e", fg="#d2dae2", padx=15, pady=15)
        self.out.pack(fill="both", expand=True)

    def _add_feature(self):
        row = ttk.Frame(self.scroll_frame, relief="groove", borderwidth=1)
        row.pack(fill="x", pady=3, padx=2)
        idx = len(self.features) + 1
        
        # State
        type_var = tk.StringVar(value="A10 - Bore")
        x_var, y_var = tk.StringVar(value="0.0"), tk.StringVar(value="0.0")
        plane_var = tk.StringVar(value="0.1") 
        d_var, e_var, h_var = [tk.StringVar(value="0.0") for _ in range(3)]
        tol_var = tk.StringVar(value="") 
        mac_var = tk.StringVar(value=str(900 + idx))
        comment_var = tk.StringVar(value=f"Point {idx}")
        
        # UI Layout
        top = ttk.Frame(row); top.pack(fill="x", padx=5, pady=2)
        ttk.Label(top, text=f"#{idx}", font=("Segoe UI", 9, "bold")).pack(side="left")
        cb = ttk.Combobox(top, textvariable=type_var, values=list(self.cycle_specs.keys()), state="readonly", width=18)
        cb.pack(side="left", padx=5)
        ttk.Entry(top, textvariable=comment_var, width=20).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(top, text="✖", width=3, command=lambda r=row: self._remove_feature(r)).pack(side="right")
        
        mid = ttk.Frame(row); mid.pack(fill="x", padx=5, pady=2)
        ttk.Label(mid, text="X:").pack(side="left")
        ttk.Entry(mid, textvariable=x_var, width=7).pack(side="left", padx=2)
        ttk.Label(mid, text="Y:").pack(side="left")
        ttk.Entry(mid, textvariable=y_var, width=7).pack(side="left", padx=2)
        ttk.Label(mid, text="Plane Z:").pack(side="left")
        ttk.Entry(mid, textvariable=plane_var, width=7).pack(side="left", padx=2)

        args_f = ttk.Frame(row); args_f.pack(fill="x", padx=5, pady=2)
        entries = {}
        for char, var in [("D", d_var), ("E", e_var), ("H", h_var)]:
            ttk.Label(args_f, text=f"{char}:").pack(side="left")
            ent = ttk.Entry(args_f, textvariable=var, width=7)
            ent.pack(side="left", padx=2)
            entries[char] = ent

        bot = ttk.Frame(row); bot.pack(fill="x", padx=5, pady=2)
        ttk.Label(bot, text="Tol:").pack(side="left")
        ttk.Entry(bot, textvariable=tol_var, width=8).pack(side="left", padx=2)
        ttk.Label(bot, text="Target Macro: #").pack(side="left")
        ttk.Entry(bot, textvariable=mac_var, width=6).pack(side="left", padx=2)

        def update_locks(*args):
            spec = self.cycle_specs[type_var.get()]
            req = spec["req"]
            for char, widget in entries.items():
                widget.config(state="normal" if char in req else "disabled")
        
        type_var.trace_add("write", update_locks)
        update_locks()

        self.features.append({
            "frame": row, "type": type_var, "x": x_var, "y": y_var, 
            "plane": plane_var, "d": d_var, "e": e_var, "h": h_var, 
            "tol": tol_var, "macro": mac_var, "comment": comment_var
        })

    def _remove_feature(self, frame):
        if len(self.features) <= 1: return
        for i, f in enumerate(self.features):
            if f["frame"] == frame:
                f["frame"].destroy()
                self.features.pop(i)
                break

    def _clear_features(self):
        for f in self.features: f["frame"].destroy()
        self.features = []
        self._add_feature()

    def _generate(self):
        if not self.features: return
        try:
            # 1. Build Feature List for Brain
            feature_list = []
            for f in self.features:
                spec = self.cycle_specs[f['type'].get()]
                feature_list.append({
                    "cycle_key": spec["key"],
                    "comment": f["comment"].get(),
                    "x": f["x"].get(),
                    "y": f["y"].get(),
                    "plane": f["plane"].get(),
                    "macro": f["macro"].get(),
                    "tol": f["tol"].get(),
                    "args": {
                        "D": f["d"].get(),
                        "E": f["e"].get(),
                        "H": f["h"].get()
                    }
                })

            # 2. Build Global Params
            params = {
                "t_num": self.tool_var.get(),
                "wcs": self.work_var.get(),
                "is_ext": self.is_ext_var.get(),
                "z_clr": self.clearance_z.get(),
                "z_protect": self.protected_z.get(),
                "features": feature_list
            }

            # 3. Request G-code from Brain (All formatting logic now happens inside Brain)
            lines = NC.generate_feature_sequence(
                params, 
                full_pgm=self.post_header_var.get(), 
                pgm_num=self.program_num_var.get(),
                use_m99=self.use_m99_var.get()
            )
            
            self.out.delete("1.0", tk.END)
            self.out.insert(tk.END, "\n".join(lines))
            
        except Exception as e:
            messagebox.showerror("Generator Error", str(e))