"""
APEXPROBE | HAAS AUTOMATION SUITE
--------------------------------
Scope: 
Modular G-Code generation tool for Haas NGC Mills, specializing in 
Renishaw WIPS (Wireless Intuitive Probing System) cycles.
Architecture:
- main.py: Application entry point and Tab/Notebook controller.
- lib/codes.py: Centralized 'Source of Truth' for Haas G/M codes.
- tabs/: Individual modules for specific machining workflows.

Author: Gemini/Olaf Gromotka Collaborative Build
Version: 1.2.3 (Fix Import Mapping)

V1.2.3 - lib/codes.py - Fixed all single surface cycles to use A20. intead of the enumerated mistake A18, A19, A20.
         lib/codes.py - Added a move to clearance height after the probing cycle
         lib/codes.py - Added a '/' "Block skip"  to the G_SAFE_XY for modularity when measuring multiple features

V1.2.4 - I need to collaborate with Gemini to hunt down the cause of the improper WCS formatting in WIPS tab linking move.
         for ex. user selects extended woffset 69: linking move outputs as G69 (not correct)
         if the user selects extended woffsegt 69: linking move SHOULD output as G154 P69
"""

import tkinter as tk
from tkinter import ttk
from tabs.wips_tab import WIPSTab
from tabs.macro_offsets_tab import MacroOffsetsTab
from tabs.flatness_tab import FlatnessTab
# Ensure this matches the filename measure_features.py exactly
from tabs.measure_features import MeasureFeaturesTab

class ApexProbe(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("ApexProbe | Haas Automation Suite")
        
        # Optimized for multi-feature lists and side-by-side G-code preview
        self.geometry("1200x900")
        self.minsize(1000, 800)
        
        # 1. Main Notebook Container
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # 2. Add Tabs
        self.wips_page = WIPSTab(self.notebook)
        self.notebook.add(self.wips_page, text=" Virtual WIPS ")
        
        # The tab logic is contained in tabs/measure_features.py
        self.measure_page = MeasureFeaturesTab(self.notebook)
        self.notebook.add(self.measure_page, text=" Measure Features ")
        
        self.flatness_page = FlatnessTab(self.notebook)
        self.notebook.add(self.flatness_page, text=" Flatness Probing ")

        self.macro_page = MacroOffsetsTab(self.notebook)
        self.notebook.add(self.macro_page, text=" Macro Offsets ")

if __name__ == "__main__":
    app = ApexProbe()
    app.mainloop()