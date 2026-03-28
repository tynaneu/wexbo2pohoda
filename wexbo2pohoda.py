#!/usr/bin/env python3
"""
Wexbo to Pohoda XML converter - GUI wrapper.

This script provides a GUI file picker and uses the updated module
with proper VAT handling, rounding, and invoiceSummary support.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from wexbo2pohoda.wexbo2pohoda import convert_xml

# ==================== GUI FILE CHOICE ====================
root = tk.Tk()
root.withdraw()

input_file = filedialog.askopenfilename(
    title="Vyber XML export z e-shopu",
    filetypes=[("XML soubory", "*.xml")]
)

if not input_file:
    raise SystemExit

# ==================== CONVERT ====================
try:
    output_file = convert_xml(input_file)
    messagebox.showinfo("Hotovo", f"Export dokončen do:\n{output_file}")
except Exception as e:
    messagebox.showerror("Chyba", f"Export selhal:\n{e}")