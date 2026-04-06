"""USRP device discovery and connection management."""

import logging

logger = logging.getLogger("TechniqueMaker.hardware.usrp")

def scan_usrps():
    """Scan for Ettus USRP devices. Returns list of dicts with serial/product."""
    try:
        import uhd
        devices = uhd.find("")
        results = []
        for dev in devices:
            results.append({
                "serial": dev.get("serial", "N/A"),
                "product": dev.get("product", "Unknown"),
                "display": f"{dev.get('serial', 'N/A')} ({dev.get('product', 'Unknown')})",
            })
        logger.info(f"Found {len(results)} USRP device(s)")
        return results
    except ImportError:
        logger.warning("UHD module not available")
        return []
    except Exception as e:
        logger.error(f"UHD scan failed: {e}")
        return []
