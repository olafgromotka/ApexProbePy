"""
APEXPROBE | Macro Offsets Dictionary (HaasMillMacros.pdf Verified)
------------------------------------------------------------------
Scope:
Fast lookup of Haas NGC macro variables for Tool and Work Offsets.
- Tool Section: Tn (1–200) lookup.
- Work Section: G52, G54–G59, and G154 P1–P99 (7k/14k banks).
- Reverse Lookup: Range-aware variable identification.
"""

import tkinter as tk
from tkinter import ttk

class MacroOffsetsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        # --- Internal Data ---
        self.AXES = ["X", "Y", "Z", "A", "B", "C"]
        
        # --- UI Variables ---
        self.tool_input = tk.StringVar(value="1")
        self.h_geom = tk.StringVar(); self.h_wear = tk.StringVar()
        self.d_geom = tk.StringVar(); self.d_wear = tk.StringVar()
        
        self.wcs_selection = tk.StringVar(value="G54")
        self.wo7 = {ax: tk.StringVar() for ax in self.AXES}
        self.wo14 = {ax: tk.StringVar() for ax in self.AXES}
        
        self.rev_input = tk.StringVar()
        self.rev_output = tk.StringVar()

        self._build_ui()
        
        # Traces for live updates
        self.tool_input.trace_add("write", lambda *a: self._update_tool_macros())
        self.wcs_selection.trace_add("write", lambda *a: self._update_work_macros())
        
        self._update_tool_macros()
        self._update_work_macros()

    def _build_ui(self):
        # Configure grid for expansion
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # 0. Header
        header_f = ttk.Frame(self, padding=(20, 10))
        header_f.grid(row=0, column=0, sticky="ew")
        ttk.Label(header_f, text="OFFSET MACRO REFERENCE", font=("Segoe UI", 14, "bold")).pack(side="left")
        ttk.Separator(self, orient="horizontal").grid(row=0, column=0, sticky="ew", pady=(40, 0))

        # Main Layout Container (Two Columns)
        main_container = ttk.Frame(self, padding=20)
        main_container.grid(row=1, column=0, sticky="nsew")
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)

        # --- LEFT COLUMN: Tool Offsets ---
        left_col = ttk.Frame(main_container, padding=(0, 0, 10, 0))
        left_col.grid(row=0, column=0, sticky="nsew")

        t_lab = ttk.LabelFrame(left_col, text=" Tool Offset Calculator ", padding=20)
        t_lab.pack(fill="both", expand=True)
        
        input_f = ttk.Frame(t_lab)
        input_f.pack(fill="x", pady=(0, 20))
        ttk.Label(input_f, text="Tool Number (1-200):", font=("Segoe UI", 10)).pack(side="left")
        ttk.Entry(input_f, textvariable=self.tool_input, width=10, font=("Segoe UI", 11)).pack(side="left", padx=10)

        # Tool Results with better visual separation
        res_f = ttk.Frame(t_lab)
        res_f.pack(fill="x")
        
        tool_headers = [
            ("H-GEOM (Length)", self.h_geom),
            ("H-WEAR (Length)", self.h_wear),
            ("D-GEOM (Diameter)", self.d_geom),
            ("D-WEAR (Diameter)", self.d_wear)
        ]
        
        for i, (lbl, var) in enumerate(tool_headers):
            row_f = ttk.Frame(res_f)
            row_f.pack(fill="x", pady=5)
            ttk.Label(row_f, text=lbl, width=20, font=("Segoe UI", 10)).pack(side="left")
            ttk.Label(row_f, textvariable=var, font=("Consolas", 12, "bold"), foreground="#d35400").pack(side="left", padx=10)

        # --- RIGHT COLUMN: Work Offsets ---
        right_col = ttk.Frame(main_container, padding=(10, 0, 0, 0))
        right_col.grid(row=0, column=1, sticky="nsew")

        w_lab = ttk.LabelFrame(right_col, text=" Work Offset Calculator ", padding=20)
        w_lab.pack(fill="both", expand=True)

        wcs_list = ["G52", "G54", "G55", "G56", "G57", "G58", "G59"] + [f"G154 P{i}" for i in range(1, 100)]
        ttk.Label(w_lab, text="Select Work Offset:", font=("Segoe UI", 10)).pack(anchor="w")
        ttk.Combobox(w_lab, textvariable=self.wcs_selection, values=wcs_list, state="readonly", font=("Segoe UI", 11)).pack(fill="x", pady=(5, 20))

        grid_f = ttk.Frame(w_lab)
        grid_f.pack(fill="x")
        
        # Grid Headers
        ttk.Label(grid_f, text="Axis", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, pady=5)
        ttk.Label(grid_f, text="7k Bank", font=("Segoe UI", 9, "bold")).grid(row=0, column=1, pady=5)
        ttk.Label(grid_f, text="14k Bank", font=("Segoe UI", 9, "bold")).grid(row=0, column=2, pady=5)

        for i, ax in enumerate(self.AXES):
            ttk.Label(grid_f, text=ax, font=("Segoe UI", 11, "bold"), width=4).grid(row=i+1, column=0, pady=4)
            ttk.Entry(grid_f, textvariable=self.wo7[ax], width=12, state="readonly", justify="center", font=("Consolas", 11)).grid(row=i+1, column=1, padx=4)
            ttk.Entry(grid_f, textvariable=self.wo14[ax], width=12, state="readonly", justify="center", font=("Consolas", 11)).grid(row=i+1, column=2, padx=4)

        # --- BOTTOM ROW: Reverse Lookup ---
        footer_f = ttk.Frame(self, padding=20)
        footer_f.grid(row=2, column=0, sticky="ew")

        rev_lab = ttk.LabelFrame(footer_f, text=" Reverse Lookup Utility ", padding=15)
        rev_lab.pack(fill="x")
        
        lookup_input_f = ttk.Frame(rev_lab)
        lookup_input_f.pack(fill="x")
        
        ttk.Label(lookup_input_f, text="Identify Macro #:").pack(side="left")
        rev_entry = ttk.Entry(lookup_input_f, textvariable=self.rev_input, width=15, font=("Consolas", 11))
        rev_entry.pack(side="left", padx=10)
        rev_entry.bind("<Return>", lambda e: self._do_reverse_lookup())
        
        ttk.Button(lookup_input_f, text="Search Variable", command=self._do_reverse_lookup).pack(side="left")
        
        self.rev_display = tk.Label(rev_lab, textvariable=self.rev_output, foreground="#27ae60", 
                                   font=("Segoe UI", 11, "italic bold"), pady=10)
        self.rev_display.pack(fill="x")

    # --- Logic Methods ---

    def _update_tool_macros(self):
        try:
            val = int(self.tool_input.get())
            if 1 <= val <= 200:
                self.h_geom.set(f"#{2000 + val}")
                self.h_wear.set(f"#{2200 + val}")
                self.d_geom.set(f"#{2400 + val}")
                self.d_wear.set(f"#{2600 + val}")
            else:
                for v in [self.h_geom, self.h_wear, self.d_geom, self.d_wear]: v.set("---")
        except:
            for v in [self.h_geom, self.h_wear, self.d_geom, self.d_wear]: v.set("---")

    def _update_work_macros(self):
        sel = self.wcs_selection.get()
        for ax in self.AXES:
            self.wo7[ax].set("")
            self.wo14[ax].set("")

        def get_axis_map(base):
            return {ax: f"#{base + i}" for i, ax in enumerate(self.AXES)}

        if sel == "G52":
            mapping = get_axis_map(5201)
            for ax in self.AXES: self.wo7[ax].set(mapping[ax])
        elif sel.startswith("G5") and " " not in sel:
            g_num = int(sel[1:])
            base = 5221 + (g_num - 54) * 20
            mapping = get_axis_map(base)
            for ax in self.AXES: self.wo7[ax].set(mapping[ax])
        elif "P" in sel:
            p = int(sel.split("P")[1])
            if 1 <= p <= 20:
                base7 = 7001 + (p-1)*20
                m7 = get_axis_map(base7)
                for ax in self.AXES: self.wo7[ax].set(m7[ax])
            if 1 <= p <= 99:
                base14 = 14001 + (p-1)*20
                m14 = get_axis_map(base14)
                for ax in self.AXES: self.wo14[ax].set(m14[ax])

    def _do_reverse_lookup(self):
        try:
            raw = self.rev_input.get().replace("#", "").strip()
            if not raw: return
            num = int(raw)
            
            # Ranges
            if 2001 <= num <= 2200: 
                self.rev_output.set(f"Tool {num-2000} - Length Geometry")
            elif 2201 <= num <= 2400: 
                self.rev_output.set(f"Tool {num-2200} - Length Wear")
            elif 2401 <= num <= 2600: 
                self.rev_output.set(f"Tool {num-2400} - Diameter Geometry")
            elif 2601 <= num <= 2800: 
                self.rev_output.set(f"Tool {num-2600} - Diameter Wear")
            elif 5201 <= num <= 5206: 
                self.rev_output.set(f"G52 Axis: {self.AXES[num-5201]}")
            elif 5221 <= num <= 5339:
                offset = (num - 5221) // 20
                g_num = 54 + offset
                ax_idx = (num - 5221) % 20
                if ax_idx < len(self.AXES): self.rev_output.set(f"G{g_num} Axis: {self.AXES[ax_idx]}")
                else: self.rev_output.set(f"G{g_num} Variable")
            elif 7001 <= num <= 7400:
                p = ((num - 7001) // 20) + 1
                ax_idx = (num - 7001) % 20
                if ax_idx < len(self.AXES): self.rev_output.set(f"G154 P{p} (7k) Axis: {self.AXES[ax_idx]}")
                else: self.rev_output.set(f"G154 P{p} (7k)")
            elif 14001 <= num <= 15980:
                p = ((num - 14001) // 20) + 1
                ax_idx = (num - 14001) % 20
                if ax_idx < len(self.AXES): self.rev_output.set(f"G154 P{p} (14k) Axis: {self.AXES[ax_idx]}")
                else: self.rev_output.set(f"G154 P{p} (14k)")
            elif num == 188:
                self.rev_output.set("Probe Result: Measured Size (Diameter/Width/Pocket)")
            else:
                self.rev_output.set("Variable outside Tool/Work offset scope.")
                    
        except ValueError:
            self.rev_output.set("Error: Enter numeric value")