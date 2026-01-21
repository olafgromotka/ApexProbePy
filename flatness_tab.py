"""
APEXPROBE | Flatness Probing Tab
------------------------------------------------------------------
Scope:
Generates G-code for multi-point flatness inspection using the 
3-stage height manager (Clearance, Protected, Plane).
- Dynamic point entry with individual macro assignment.
- Uses P9995 (WIPS Surface Z) for measurements into a sacrificial offset.
- Uses #5063 for capturing Z results.
- User-definable macros for Tolerance, Min, Max, and Dev results.
- Automatic variable initialization for a "clean slate" start.
- Block Look-Ahead Control: Uses G103 P1 during probing.
- Post-processing: Optional %, O-number, and M30/M99 termination.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from lib.codes import G43, G65, G90, G91, G00, M01, M06, PROBE_ON, PROBE_OFF, PROBE_PROTECT, G_HOME_Z, G_SAFE_XY, f_dec, format_wcs, WIPS_STORM

class FlatnessTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # --- State ---
        self.points = [] # List of dicts: {"x": SV, "y": SV, "macro": SV, "frame": Frame}
        
        # Machine Setup
        self.tool_var = tk.StringVar(value="50")
        self.work_var = tk.StringVar(value="54")
        self.is_ext_var = tk.BooleanVar(value=False)
        
        # Sacrificial Offset
        self.sac_work_var = tk.StringVar(value="97")
        self.sac_ext_var = tk.BooleanVar(value=True) 

        # Height Manager State
        self.clearance_z = tk.StringVar(value="6.0")
        self.protected_z = tk.StringVar(value="1.0")
        self.probing_plane = tk.StringVar(value="0.5")
        
        # Logic & Tolerance
        self.tolerance = tk.StringVar(value="0.001")
        self.tol_macro = tk.StringVar(value="800")
        
        # Result Macros
        self.min_macro = tk.StringVar(value="801")
        self.max_macro = tk.StringVar(value="802")
        self.dev_macro = tk.StringVar(value="803")

        # Post Processing
        self.post_wrap_var = tk.BooleanVar(value=False)
        self.o_number_var = tk.StringVar(value="01234")
        self.m30_var = tk.BooleanVar(value=False)
        self.m99_var = tk.BooleanVar(value=True) # Default checked for sub-programs
        
        self._build_ui()
        
        # Initial default points
        self._add_point(x="1.0", y="1.0")
        self._add_point(x="1.0", y="-1.0")
        self._add_point(x="-1.0", y="-1.0")
        self._add_point(x="-1.0", y="1.0")

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1) 

        # --- LEFT PANEL ---
        input_panel = ttk.Frame(self)
        input_panel.grid(row=0, column=0, sticky="nsw", padx=(20, 10), pady=10)

        # 1. Machine Setup
        setup_f = ttk.LabelFrame(input_panel, text=" Machine Setup ", padding=10)
        setup_f.pack(fill="x", pady=(0, 10))
        
        r_tool = ttk.Frame(setup_f); r_tool.pack(fill="x", pady=2)
        ttk.Label(r_tool, text="Probe Tool #:", width=14).pack(side="left")
        ttk.Entry(r_tool, textvariable=self.tool_var, width=8).pack(side="left")

        r_work = ttk.Frame(setup_f); r_work.pack(fill="x", pady=2)
        ttk.Label(r_work, text="Active Offset:", width=14).pack(side="left")
        ttk.Entry(r_work, textvariable=self.work_var, width=8).pack(side="left")
        ttk.Checkbutton(r_work, text="Ext", variable=self.is_ext_var).pack(side="left", padx=5)

        r_sac = ttk.Frame(setup_f); r_sac.pack(fill="x", pady=2)
        ttk.Label(r_sac, text="Sacrificial #:", width=14).pack(side="left")
        ttk.Entry(r_sac, textvariable=self.sac_work_var, width=8).pack(side="left")
        ttk.Checkbutton(r_sac, text="Ext", variable=self.sac_ext_var).pack(side="left", padx=5)

        # 2. Height Manager
        phys_f = ttk.LabelFrame(input_panel, text=" 3-Stage Height Manager ", padding=10)
        phys_f.pack(fill="x", pady=(0, 10))
        
        for label, var in [("1. Clearance Z:", self.clearance_z), 
                          ("2. Protected Z:", self.protected_z), 
                          ("3. Probe Plane:", self.probing_plane)]:
            r = ttk.Frame(phys_f); r.pack(fill="x", pady=2)
            ttk.Label(r, text=label, width=14).pack(side="left")
            ttk.Entry(r, textvariable=var, width=8).pack(side="left")

        # 3. Logic & Results
        logic_f = ttk.LabelFrame(input_panel, text=" Logic & Result Macros ", padding=10)
        logic_f.pack(fill="x", pady=(0, 10))

        tol_r = ttk.Frame(logic_f); tol_r.pack(fill="x", pady=(2, 8))
        ttk.Label(tol_r, text="Tol:", width=5).pack(side="left")
        ttk.Entry(tol_r, textvariable=self.tolerance, width=8).pack(side="left")
        ttk.Label(tol_r, text=" @ #").pack(side="left")
        ttk.Entry(tol_r, textvariable=self.tol_macro, width=6, foreground="#2980b9").pack(side="left")

        ana_r = ttk.Frame(logic_f); ana_r.pack(fill="x", pady=2)
        ttk.Label(ana_r, text="Min#").pack(side="left")
        ttk.Entry(ana_r, textvariable=self.min_macro, width=5).pack(side="left", padx=2)
        ttk.Label(ana_r, text="Max#").pack(side="left")
        ttk.Entry(ana_r, textvariable=self.max_macro, width=5).pack(side="left", padx=2)
        ttk.Label(ana_r, text="Dev#").pack(side="left")
        ttk.Entry(ana_r, textvariable=self.dev_macro, width=5).pack(side="left", padx=2)

        # 4. Post Processing (Updated for Conditional UI)
        self.post_f = ttk.LabelFrame(input_panel, text=" Post Processing ", padding=10)
        self.post_f.pack(fill="x", pady=(0, 10))
        
        ttk.Checkbutton(self.post_f, text="Post with % & O-Number", 
                        variable=self.post_wrap_var, 
                        command=self._update_post_visibility).pack(anchor="w")
        
        # Sub-container for conditional options
        self.post_options_f = ttk.Frame(self.post_f)
        
        r_onum = ttk.Frame(self.post_options_f); r_onum.pack(fill="x", pady=5)
        ttk.Label(r_onum, text="O-Number:").pack(side="left")
        ttk.Entry(r_onum, textvariable=self.o_number_var, width=10).pack(side="left", padx=5)
        
        term_r = ttk.Frame(self.post_options_f); term_r.pack(fill="x", pady=(5,0))
        ttk.Checkbutton(term_r, text="Include M30", variable=self.m30_var, command=lambda: self._toggle_m(30)).pack(side="left")
        ttk.Checkbutton(term_r, text="Include M99", variable=self.m99_var, command=lambda: self._toggle_m(99)).pack(side="left", padx=10)

        # Initialize visibility based on default state
        self._update_post_visibility()

        # 5. Points List
        self.points_lab = ttk.LabelFrame(input_panel, text=" Inspection Points ", padding=10)
        self.points_lab.pack(fill="both", expand=True)
        
        pt_btn_f = ttk.Frame(self.points_lab)
        pt_btn_f.pack(fill="x", pady=(0, 10))
        ttk.Button(pt_btn_f, text="+ Add Point", command=self._add_point, width=12).pack(side="left", padx=2)
        ttk.Button(pt_btn_f, text="Clear All", command=self._clear_points, width=12).pack(side="left", padx=2)
        
        self.points_container = ttk.Frame(self.points_lab)
        self.points_container.pack(fill="both", expand=True)

        # --- RIGHT PANEL: OUTPUT ---
        output_panel = ttk.Frame(self)
        output_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=10)
        
        action_f = ttk.Frame(output_panel)
        action_f.pack(fill="x", pady=(0, 5))
        
        ttk.Button(action_f, text="GENERATE", command=self._generate_code, style="Accent.TButton").pack(side="left", fill="x", expand=True, padx=(0, 2))
        ttk.Button(action_f, text="CLEAR", command=self._clear_output).pack(side="left", fill="x", expand=True, padx=2)
        ttk.Button(action_f, text="COPY OUTPUT", command=self._copy_output).pack(side="left", fill="x", expand=True, padx=(2, 0))

        self.output_text = tk.Text(
            output_panel, font=("Consolas", 11), bg="#1e272e", fg="#d2dae2", 
            padx=15, pady=15, undo=True, borderwidth=0, relief="flat"
        )
        self.output_text.pack(fill="both", expand=True)

    def _update_post_visibility(self):
        """Shows or hides post-processing details based on the main checkbox."""
        if self.post_wrap_var.get():
            self.post_options_f.pack(fill="x", pady=(5, 0))
        else:
            self.post_options_f.pack_forget()

    def _toggle_m(self, code):
        """Mutex for M30 and M99 selection."""
        if code == 30 and self.m30_var.get():
            self.m99_var.set(False)
        elif code == 99 and self.m99_var.get():
            self.m30_var.set(False)

    def _add_point(self, x="0.0", y="0.0"):
        row = ttk.Frame(self.points_container)
        row.pack(fill="x", pady=2)
        next_m = 901
        if self.points:
            try: next_m = int(self.points[-1]["macro"].get()) + 1
            except: pass

        x_var = tk.StringVar(value=x); y_var = tk.StringVar(value=y); m_var = tk.StringVar(value=str(next_m))
        ttk.Label(row, text=f"P{len(self.points)+1}:", width=4, font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Label(row, text="X").pack(side="left", padx=(5, 0))
        ttk.Entry(row, textvariable=x_var, width=8).pack(side="left", padx=2)
        ttk.Label(row, text="Y").pack(side="left", padx=(5, 0))
        ttk.Entry(row, textvariable=y_var, width=8).pack(side="left", padx=2)
        ttk.Label(row, text="#").pack(side="left", padx=(5, 0))
        ttk.Entry(row, textvariable=m_var, width=5, foreground="#2980b9").pack(side="left", padx=2)
        ttk.Button(row, text="✖", width=3, command=lambda r=row: self._remove_point(r)).pack(side="right", padx=5)
        self.points.append({"x": x_var, "y": y_var, "macro": m_var, "frame": row})

    def _remove_point(self, frame):
        if len(self.points) <= 2: return
        for i, p in enumerate(self.points):
            if p["frame"] == frame:
                p["frame"].destroy()
                self.points.pop(i)
                break

    def _clear_points(self):
        for p in self.points: p["frame"].destroy()
        self.points = []
        self._add_point(); self._add_point()

    def _clear_output(self):
        self.output_text.delete("1.0", tk.END)

    def _copy_output(self):
        content = self.output_text.get("1.0", tk.END).strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)

    def _generate_code(self):
        if len(self.points) < 2: return
        try:
            t_num = self.tool_var.get()
            g_work, _ = format_wcs(self.work_var.get(), self.is_ext_var.get())
            _, w_sac = format_wcs(self.sac_work_var.get(), self.sac_ext_var.get())

            z_clr = f_dec(self.clearance_z.get())
            z_prot = f_dec(self.protected_z.get())
            
            tol_val = f_dec(self.tolerance.get())
            t_mac = self.tol_macro.get().replace("#", "")
            min_mac = self.min_macro.get().replace("#", "")
            max_mac = self.max_macro.get().replace("#", "")
            dev_mac = self.dev_macro.get().replace("#", "")
            first_pt_mac = self.points[0]["macro"].get().replace("#", "")
            
            o_num = self.o_number_var.get().strip().upper().replace("O", "")
            if not o_num: o_num = "01234"
        except Exception as e:
            messagebox.showerror("Input Error", f"Check inputs: {e}")
            return

        lines = []
        # Post-wrap logic still applies internally if the user has it toggled
        is_wrapped = self.post_wrap_var.get()

        if is_wrapped:
            lines.extend(["%", f"O{o_num}"])

        lines.extend([
            "(--- 3-STAGE FLATNESS ROUTINE ---)",
            f"(USING SACRIFICIAL OFFSET {w_sac} FOR DUMP)",
            "G103 P1 (LIMIT LOOK-AHEAD)",
            "",
            "(INITIALIZE VARIABLES - CLEAN SLATE)"
        ])

        for pt in self.points:
            p_mac = pt["macro"].get().replace("#", "")
            lines.append(f"#{p_mac}=0. (RESET P{self.points.index(pt)+1})")
        
        lines.append(f"#{min_mac}=0. (RESET MIN)")
        lines.append(f"#{max_mac}=0. (RESET MAX)")
        lines.append(f"#{dev_mac}=0. (RESET DEV)")
        lines.append(f"#{t_mac}={tol_val} (SET TOLERANCE)")
        
        lines.extend([
            "",
            f"{G_HOME_Z}",
            f"{G_SAFE_XY}",
            f"T{t_num} {M06} (PROBE)",
            f"{G90} {g_work} (ACTIVE WORK OFFSET)",
            f"{G43} H{t_num} Z{z_clr} (1. CLEARANCE)",
            f"{PROBE_ON}",
            ""
        ])

        for i, pt in enumerate(self.points):
            p_mac = pt["macro"].get().replace("#", "")
            x_val = f_dec(pt['x'].get())
            y_val = f_dec(pt['y'].get())
            lines.append(f"(POINT {i+1} -> #{p_mac})")
            lines.append(f"{PROBE_PROTECT} X{x_val} Y{y_val} Z{z_prot}")
            lines.append(f"{WIPS_STORM} {w_sac} A20. H-1.0 (SURFACE Z)")
            lines.append(f"#{p_mac}=#5063 (CAPTURE Z MACHINE POS)")
            lines.append("")

        lines.append(f"{PROBE_OFF}")
        lines.append(f"{G_HOME_Z}")
        lines.append(f"{G_SAFE_XY}")
        lines.append(f"{M01}")
        lines.append("")
        lines.append("(--- CALCULATE MIN/MAX RANGE ---)")
        lines.append(f"#{min_mac}=#{first_pt_mac} (SEED MIN)")
        lines.append(f"#{max_mac}=#{first_pt_mac} (SEED MAX)")
        
        for i in range(1, len(self.points)):
            p_mac = self.points[i]["macro"].get().replace("#", "")
            lines.append(f"IF [#{p_mac} LT #{min_mac}] THEN #{min_mac}=#{p_mac}")
            lines.append(f"IF [#{p_mac} GT #{max_mac}] THEN #{max_mac}=#{p_mac}")

        lines.append("")
        lines.append(f"#{dev_mac}=[#{max_mac}-#{min_mac}]")
        lines.append(f"IF [#{dev_mac} GT #{t_mac}] #3000=1 (FLATNESS TOL EXCEEDED)")
        lines.append("(FLATNESS WITHIN LIMITS)")
        lines.append("G103 P0 (RESTORE LOOK-AHEAD)")
        
        # Termination (Only if wrapped)
        if is_wrapped:
            if self.m30_var.get():
                lines.append("M30")
            elif self.m99_var.get():
                lines.append("M99")
            else:
                lines.append(f"{M01}")
            lines.append("%")
        else:
            lines.append(f"{M01}")

        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, "\n".join(lines))