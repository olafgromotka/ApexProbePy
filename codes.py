"""
ApexProbe | lib/codes.py
G & M code definitions & combos
"""

# --- G CODES (Lobby / Global Scope) ---
G00  = "G00"
G01  = "G01"
G28  = "G28"
G43  = "G43"
G65  = "G65"
G90  = "G90"
G91  = "G91"
G103 = "G103"
G154 = "G154"

# --- M CODES ---
M01 = "M01"
M06 = "M06"
M09 = "M09"
M30 = "M30"
M99 = "M99"

# --- HAAS MACRO DEFINITIONS ---
# Legal User Macro Variables for data storage/offsetting
haas_user_macros = [
    range(100, 147),
    range(200, 550),
    range(600, 700),
    range(800, 1000)
]

# --- RENISHAW MACRO CONSTANTS ---
PROBE_ON      = "G65 P9832"
PROBE_OFF     = "G65 P9833"
PROBE_PROTECT = "G65 P9810"
WIPS_STORM    = "G65 P9995"

# --- SAFETY / LINKING ---
G_HOME_Z  = f"{G00} {G91} {G28} Z0."
G_SAFE_XY = f"{G00} {G90} {G154} P99 X0. Y0."


def f_dec(value):  # Helper function for formatting decimals
    try:
        s = str(value).strip()
        if not s:
            return "0."
        return s if "." in s else f"{s}."
    except:
        return "0."


def format_wcs(wcs_num, is_ext):  
    """
    Formats the WCS for G-code (G54) and the WIPS macro argument (W54.).
    """
    try:
        val = int(str(wcs_num).upper().replace("G", "").strip())
        if is_ext:
            p_fmt = str(val).zfill(2)
            return f"G154 P{val}", f"W154.{p_fmt}"
        else:
            return f"G{val}", f"W{val}."
    except ValueError:
        clean_val = str(wcs_num).upper().replace("G", "").strip()
        return f"G{clean_val}", f"W{clean_val}."


def collect_user_params(t_num, wcs, probe_cycle, z_clr, z_protect, probe_plane, xpos, ypos, is_ext=False, args_dict=None):
    """Collects and returns a single dict of user params."""
    return {
        "t_num": int(float(t_num or 0)),
        "wcs": str(wcs).strip(),
        "probe_cycle": str(probe_cycle).strip(),
        "z_clr": float(z_clr),
        "z_protect": float(z_protect),
        "probe_plane": float(probe_plane),
        "xpos": float(xpos),
        "ypos": float(ypos),
        "is_ext": bool(is_ext),
        "args_dict": args_dict or {},
    }


def generate_cycle_line(cycle_key, args_dict, wcs, is_ext):
    """
    Builds the G65 P9995 macro line based on cycle key and arguments.
    """
    _, w_macro = format_wcs(wcs, is_ext)

    # Standard Arg Extraction (Handles both upper and lower case from UI)
    d = f_dec(args_dict.get("D", args_dict.get("d", "0")))
    e = f_dec(args_dict.get("E", args_dict.get("e", "0")))
    h = f_dec(args_dict.get("H", args_dict.get("h", "0")))
    i = f_dec(args_dict.get("I", args_dict.get("i", "0")))

    # Cycle Mappings
    if cycle_key == "A10": return f"{WIPS_STORM} A10. D{d} {w_macro}"
    if cycle_key == "A11": return f"{WIPS_STORM} A11. D{d} H{h} {w_macro}"
    if cycle_key == "A12": return f"{WIPS_STORM} A12. D{d} E{e} {w_macro}"
    if cycle_key == "A13": return f"{WIPS_STORM} A13. D{d} E{e} H{h} {w_macro}"
    if cycle_key == "A14": return f"{WIPS_STORM} A14. D{d} H{h} {w_macro}"
    if cycle_key == "A15": return f"{WIPS_STORM} A15. D{d} {w_macro}"
    if cycle_key == "A16": return f"{WIPS_STORM} A16. E{e} H{h} {w_macro}"
    if cycle_key == "A17": return f"{WIPS_STORM} A17. E{e} {w_macro}"
    if cycle_key == "A20Z": return f"{WIPS_STORM} A20. H{h} {w_macro}"
    if cycle_key == "A20X": return f"{WIPS_STORM} A20. D{d} {w_macro}"
    if cycle_key == "A20Y": return f"{WIPS_STORM} A20. E{e} {w_macro}"
    
    return f"(ERROR: UNKNOWN CYCLE {cycle_key})"


def generate_toolpath(params: dict):
    """Build single toolpath sandwich."""
    t_num       = params["t_num"]
    wcs         = params["wcs"]
    cycle_key   = params["probe_cycle"]
    z_clr       = params["z_clr"]
    z_protect   = params["z_protect"]
    probe_plane = params["probe_plane"]
    xpos        = params["xpos"]
    ypos        = params["ypos"]
    is_ext      = params["is_ext"]
    args_dict   = params["args_dict"]

    g_wcs, _ = format_wcs(wcs, is_ext=is_ext)
    cycle_line = generate_cycle_line(cycle_key, args_dict, wcs, is_ext=is_ext)

    toolpath = [
        "",
        G_HOME_Z,
        G_SAFE_XY,
        f"T{t_num} {M06}",
        f"{G00} {G90} {g_wcs} X{f_dec(xpos)} Y{f_dec(ypos)}",
        f"{G43} H{t_num} Z{f_dec(z_clr)}",
        f"{G00} Z{f_dec(z_protect)}",
        PROBE_ON,
        f"{PROBE_PROTECT} Z{f_dec(probe_plane)}",
        "",
        cycle_line,
        "",
        PROBE_OFF,
        f"{G43} H{t_num} Z{f_dec(z_clr)}",
        f"{G_HOME_Z}",
        f"{G_SAFE_XY}",
        f"{M01}",
        ""
    ]
    return toolpath


def generate_feature_sequence(params: dict, full_pgm=False, pgm_num="1234", use_m99=False):
    """
    Builds a sequential measurement toolpath for multiple features.
    
    Safety Logic:
    - ALWAYS homes and clears before Tool Change.
    - ALWAYS homes and clears after probing completes.
    - full_pgm only controls O-num, %, and M30/M99 termination.
    """
    t_num_raw  = params.get("t_num", "0")
    wcs        = params["wcs"]
    is_ext     = params["is_ext"]
    z_clr      = params["z_clr"]
    z_protect  = params["z_protect"]
    features   = params.get("features", [])

    # Ensure tool number is an integer for N-line math
    try:
        t_int = int(float(t_num_raw))
    except:
        t_int = 0

    g_wcs, _ = format_wcs(wcs, is_ext=is_ext)

    # 1. Opening: Safety first, then tool change
    lines = [
        "",
        "(MULTI-FEATURE MEASUREMENT ROUTINE)",
        f"{G103} P1 (LIMIT LOOK-AHEAD)",
        "(RESET FEATURE MACROS)",
    ]
    
    for feat in features:
        mac = str(feat.get("macro", feat.get("macro_num", ""))).replace("#", "").strip()
        if mac: lines.append(f"#{mac} = 0.")

    lines.extend([
        "",
        G_HOME_Z,
        G_SAFE_XY,
        f"T{t_int} {M06} (PROBE TOOL)",
        f"{G00} {G90} {g_wcs}",
        f"{G43} H{t_int} Z{f_dec(z_clr)}",
        PROBE_ON
    ])

    # 2. Sequential Probing
    for i, feat in enumerate(features):
        comment = feat.get("comment", f"FEATURE {i+1}").strip()
        x       = f_dec(feat.get("x", "0"))
        y       = f_dec(feat.get("y", "0"))
        plane   = f_dec(feat.get("plane", "0"))
        macro   = str(feat.get("macro", feat.get("macro_num", ""))).replace("#", "").strip()
        tol     = str(feat.get("tol", feat.get("tolerance", ""))).strip()
        args    = feat.get("args", {})
        
        # Calculate N-Number: (Tool * 100) + (Index + 1)
        n_val = (t_int * 100) + (i + 1)

        # SMART NOMINAL LOGIC
        nominal = feat.get("nominal", "").strip()
        if not nominal:
            ck = feat.get("cycle_key", "")
            if ck in ["A10", "A11", "A14", "A15", "A20X"]: 
                nominal = args.get("D", args.get("d", ""))
            elif ck in ["A16", "A17", "A20Y"]: 
                nominal = args.get("E", args.get("e", ""))
            elif ck == "A20Z": 
                nominal = args.get("H", args.get("h", ""))
            elif ck in ["A12", "A13"]: 
                nominal = args.get("D", args.get("d", ""))

        lines.append("")
        lines.append(f"N{n_val} ({comment.upper()}: {feat['cycle_key']})")
        lines.append(f"{G00} X{x} Y{y}")
        lines.append(f"{G00} Z{f_dec(z_protect)}")
        lines.append(f"{PROBE_PROTECT} Z{plane} F50.")
        
        cycle_line = generate_cycle_line(feat["cycle_key"], args, wcs, is_ext)
        lines.append(cycle_line)

        if macro:
            lines.append(f"#{macro} = #188 (STORE MEASURED)")
            
            if tol and nominal:
                nom_val = f_dec(nominal)
                tol_val = f_dec(tol)
                lines.append(f"(--- {comment.upper()} EVALUATION ---)")
                lines.append(f"#100 = ABS[ #{macro} - {nom_val} ] (DEVIATION)")
                lines.append(f"IF [ #100 GT {tol_val} ] #3000 = 1 ({comment.upper()} OUT OF TOL)")
        
        lines.append(f"{G00} Z{f_dec(z_clr)}")

    # 3. Closing: Mandatory safety linking
    lines.extend([
        "",
        PROBE_OFF,
        f"{G103} P0 (RESTORE LOOK-AHEAD)",
        G_HOME_Z,
        G_SAFE_XY,
        ""
    ])

    # 4. Administrative Wrapping (O-Num, %, M30/M99)
    if full_pgm:
        lines.insert(0, "%")
        o_val = str(pgm_num).upper().replace("O", "").strip()
        lines.insert(1, f"O{o_val} (APEXPROBE MEASURE)")
        
        # Append termination
        lines.append(M99 if use_m99 else M30)
        lines.append("%")

    return lines


def get_cycle_metadata(selection):
    """ROOT SOURCE OF TRUTH for cycle arguments and helper text."""
    if "A10" in selection:
        return "Bore (A10): D = Target Diameter.", {"d": "1.0", "e": "0", "h": "0"}, {"d": True, "e": False, "h": False}
    elif "A11" in selection:
        return "Boss (A11): D = Diameter, H = Z-depth for probing.", {"d": "1.0", "e": "0", "h": "-0.5"}, {"d": True, "e": False, "h": True}
    elif "A12" in selection:
        return "Rect Pocket (A12): D = X Width, E = Y Width.", {"d": "1.0", "e": "1.0", "h": "0"}, {"d": True, "e": True, "h": False}
    elif "A13" in selection:
        return "Rect Boss (A13): D = X Width, E = Y Width, H = Z-depth.", {"d": "1.0", "e": "1.0", "h": "-0.5"}, {"d": True, "e": True, "h": True}
    elif "A14" in selection:
        return "Web X (A14): D = Width, H = Z-depth.", {"d": "1.0", "e": "0", "h": "-0.5"}, {"d": True, "e": False, "h": True}
    elif "A15" in selection:
        return "Pocket X (A15): D = Width.", {"d": "1.0", "e": "0", "h": "0"}, {"d": True, "e": False, "h": False}
    elif "A16" in selection:
        return "Web Y (A16): E = Width, H = Z-depth.", {"d": "0", "e": "1.0", "h": "-0.5"}, {"d": False, "e": True, "h": True}
    elif "A17" in selection:
        return "Pocket Y (A17): E = Width.", {"d": "0", "e": "1.0", "h": "0"}, {"d": False, "e": True, "h": False}
    elif "Surface Z" in selection:
        return "Z Surface (A20): H = Direction (Generator forces negative).", {"d": "0", "e": "0", "h": "-1.0"}, {"d": False, "e": False, "h": True}
    elif "Surface X" in selection:
        return "X Surface (A20): D = Approach direction/dist.", {"d": "1.0", "e": "0", "h": "0"}, {"d": True, "e": False, "h": False}
    elif "Surface Y" in selection:
        return "Y Surface (A20): E = Approach direction/dist.", {"d": "0", "e": "1.0", "h": "0"}, {"d": False, "e": True, "h": False}

    return "Selection Error.", {"d": "0", "e": "0", "h": "0"}, {"d": True, "e": True, "h": True}