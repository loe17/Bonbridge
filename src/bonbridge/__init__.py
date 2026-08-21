"""BonBridge - turn a Linux box into a network receipt printer for POS apps.

BonBridge exposes locally attached (USB / serial) ESC/POS receipt printers as
plain RAW/JetDirect network printers on TCP port 9100, so that POS
applications which can only address a printer by IP address - such as
OrderAssist - can print to them.

See docs/ for the full documentation (German and English).
"""

__version__ = "1.3.0"
__all__ = ["__version__"]
