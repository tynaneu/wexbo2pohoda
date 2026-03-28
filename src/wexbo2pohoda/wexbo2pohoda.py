import xml.etree.ElementTree as ET
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import logging
import traceback

# ==================== SETTINGS ====================
CISLENA_RADA = "ESHOP"
TEXT_POLOZKY = "Zboží / služby – e-shop"

# ==================== NAMESPACES ====================
NS_DAT = "http://www.stormware.cz/schema/version_2/data.xsd"
NS_INV = "http://www.stormware.cz/schema/version_2/invoice.xsd"
NS_TYP = "http://www.stormware.cz/schema/version_2/type.xsd"

ET.register_namespace("dat", NS_DAT)
ET.register_namespace("inv", NS_INV)
ET.register_namespace("typ", NS_TYP)

# ==================== FUNCTIONS ====================
def iso_date(d):
    try:
        return datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(d, "%d.%m.%Y").strftime("%Y-%m-%d")
        except:
            return datetime.now().strftime("%Y-%m-%d")

def get_text(parent, tag):
    v = parent.findtext(tag) or ""
    return v.strip()

def detect_vat(item):
    high = get_text(item, "price_high")
    low = get_text(item, "price_low")
    if high and float(high) > 0:
        return "high", high
    if low and float(low) > 0:
        return "low", low
    return "none", get_text(item, "price_none") or "0"

def load_source_xml(input_file):
    """Load and parse source XML file.
    
    Args:
        input_file: Path to input XML file
    
    Returns:
        List of order elements
    
    Raises:
        Exception: If XML cannot be parsed
    """
    try:
        tree = ET.parse(input_file)
        src_root = tree.getroot()
        orders = src_root.findall("item")
        return orders
    except Exception as e:
        logging.error(f"Failed to load XML: {e}")
        raise

def generate_output_filename(input_file):
    """Generate output filename based on input file and timestamp.
    
    Args:
        input_file: Path to input XML file
    
    Returns:
        Generated output file path
    """
    base_dir = os.path.dirname(input_file)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(base_dir, f"pohoda_import_{timestamp}.xml")

def create_datapack_root(supplier_ico):
    """Create root dataPack element.
    
    Args:
        supplier_ico: Supplier ICO number
    
    Returns:
        ET.Element: Root dataPack element
    """
    datapack = ET.Element(
        f"{{{NS_DAT}}}dataPack",
        {
            "id": "WEXBO",
            "ico": supplier_ico,
            "application": "Wexbo import",
            "version": "2.0",
            "note": "Import faktur z e-shopu",
        },
    )
    return datapack

def create_invoice_header(header, order):
    """Create invoice header with basic information.
    
    Args:
        header: Parent header element
        order: Order XML element
    """
    inv_id = get_text(order, "invoice_id")
    
    ET.SubElement(header, f"{{{NS_INV}}}invoiceType").text = "issuedInvoice"
    
    num_el = ET.SubElement(header, f"{{{NS_INV}}}number")
    ET.SubElement(num_el, f"{{{NS_TYP}}}numberRequested").text = inv_id
    
    ET.SubElement(header, f"{{{NS_INV}}}text").text = f"Wexbo {inv_id}"
    ET.SubElement(header, f"{{{NS_INV}}}date").text = iso_date(get_text(order, "date_create"))
    ET.SubElement(header, f"{{{NS_INV}}}dateTax").text = iso_date(get_text(order, "date_delivery"))
    ET.SubElement(header, f"{{{NS_INV}}}dateDue").text = iso_date(get_text(order, "date_due"))

def create_partner_identity(header, order):
    """Create partner identity section with billing information.
    
    Args:
        header: Parent header element
        order: Order XML element
    """
    partner = ET.SubElement(header, f"{{{NS_INV}}}partnerIdentity")
    addr = ET.SubElement(partner, f"{{{NS_TYP}}}address")
    
    ET.SubElement(addr, f"{{{NS_TYP}}}company").text = get_text(order, "billing_name")
    ET.SubElement(addr, f"{{{NS_TYP}}}street").text = f"{get_text(order, 'billing_street')} {get_text(order, 'billing_street_number')}".strip()
    ET.SubElement(addr, f"{{{NS_TYP}}}city").text = get_text(order, "billing_town")
    ET.SubElement(addr, f"{{{NS_TYP}}}zip").text = get_text(order, "billing_zip")
    
    country_val = get_text(order, "billing_state")
    if country_val:
        country_el = ET.SubElement(addr, f"{{{NS_TYP}}}country")
        ET.SubElement(country_el, f"{{{NS_TYP}}}ids").text = country_val

def create_activity(header):
    """Create activity section.
    
    Args:
        header: Parent header element
    """
    activity = ET.SubElement(header, f"{{{NS_INV}}}activity")
    ET.SubElement(activity, f"{{{NS_TYP}}}ids").text = "Pom"

def create_invoice_items(invoice, order):
    """Create invoice items section.
    
    Args:
        invoice: Parent invoice element
        order: Order XML element
    """
    vat_rate, base_price = detect_vat(order)
    detail = ET.SubElement(invoice, f"{{{NS_INV}}}invoiceDetail")
    inv_item = ET.SubElement(detail, f"{{{NS_INV}}}invoiceItem")
    
    ET.SubElement(inv_item, f"{{{NS_INV}}}text").text = TEXT_POLOZKY
    ET.SubElement(inv_item, f"{{{NS_INV}}}quantity").text = "1"
    ET.SubElement(inv_item, f"{{{NS_INV}}}unit").text = "ks"
    ET.SubElement(inv_item, f"{{{NS_INV}}}rateVAT").text = vat_rate
    
    home_curr = ET.SubElement(inv_item, f"{{{NS_INV}}}homeCurrency")
    ET.SubElement(home_curr, f"{{{NS_TYP}}}unitPrice").text = base_price

def create_invoice_element(datapack, order, idx):
    """Create complete invoice element for an order.
    
    Args:
        datapack: Parent dataPack element
        order: Order XML element
        idx: Invoice index number
    
    Returns:
        ET.Element: Created invoice element
    """
    pack_item = ET.SubElement(
        datapack,
        f"{{{NS_DAT}}}dataPackItem",
        {
            "id": str(idx),
            "version": "2.0",
        },
    )
    
    invoice = ET.SubElement(pack_item, f"{{{NS_INV}}}invoice", {"version": "2.0"})
    header = ET.SubElement(invoice, f"{{{NS_INV}}}invoiceHeader")
    
    create_invoice_header(header, order)
    create_partner_identity(header, order)
    create_activity(header)
    create_invoice_items(invoice, order)
    
    return invoice

def write_output_xml(datapack, output_file):
    """Write XML tree to output file.
    
    Args:
        datapack: Root dataPack element
        output_file: Path to output file
    
    Raises:
        Exception: If file cannot be written
    """
    try:
        with open(output_file, "wb") as f:
            tree_out = ET.ElementTree(datapack)
            tree_out.write(f, encoding="utf-8", xml_declaration=True)
        logging.info(f"Successfully converted to {output_file}")
    except Exception as e:
        logging.error(f"Failed to write output: {traceback.format_exc()}")
        raise

def convert_xml(input_file, output_file=None):
    """Convert e-shop XML export to Pohoda format.
    
    Args:
        input_file: Path to input XML file
        output_file: Path to output XML file (optional, auto-generated if not provided)
    
    Returns:
        Path to the generated output file
    """
    orders = load_source_xml(input_file)
    
    if output_file is None:
        output_file = generate_output_filename(input_file)
    
    supplier_ico = get_text(orders[0], "supplier_ico")
    datapack = create_datapack_root(supplier_ico)
    
    for idx, order in enumerate(orders, start=1):
        create_invoice_element(datapack, order, idx)
    
    write_output_xml(datapack, output_file)
    return output_file

def main():
    """Main entry point with GUI file selection."""
    # ==================== GUI FILE CHOICE ====================
    root = tk.Tk()
    root.withdraw()

    input_file = filedialog.askopenfilename(
        title="Vyber XML export z e-shopu",
        filetypes=[("XML soubory", "*.xml")]
    )

    if not input_file:
        raise SystemExit

    # ==================== LOGGING ====================
    base_dir = os.path.dirname(input_file)
    log_file = os.path.join(base_dir, "wexbo_to_pohoda.log")

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    try:
        output_file = convert_xml(input_file)
        messagebox.showinfo("Hotovo", f"Export dokončen do:\n{output_file}")
    except Exception as e:
        logging.error(traceback.format_exc())
        messagebox.showerror("Chyba", "Export selhal při zápisu.")
        raise SystemExit

if __name__ == "__main__":
    main()
