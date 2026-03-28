import pytest
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wexbo2pohoda.wexbo2pohoda import convert_xml, get_text, detect_vat, iso_date, round_price, get_vat_items


@pytest.fixture
def sample_xml_path():
    """Return path to sample XML fixture."""
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_export.xml')


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestConversion:
    """Integration tests for XML conversion."""

    def test_convert_xml_creates_output_file(self, sample_xml_path, temp_output_dir):
        """Test that conversion creates an output file."""
        output_file = os.path.join(temp_output_dir, 'output.xml')
        result = convert_xml(sample_xml_path, output_file)
        
        assert os.path.exists(result)
        assert result == output_file

    def test_output_is_valid_xml(self, sample_xml_path, temp_output_dir):
        """Test that output is valid XML."""
        output_file = os.path.join(temp_output_dir, 'output.xml')
        convert_xml(sample_xml_path, output_file)
        
        tree = ET.parse(output_file)
        root = tree.getroot()
        assert root is not None

    def test_output_has_correct_namespace(self, sample_xml_path, temp_output_dir):
        """Test that output has correct Pohoda namespaces."""
        output_file = os.path.join(temp_output_dir, 'output.xml')
        convert_xml(sample_xml_path, output_file)
        
        tree = ET.parse(output_file)
        root = tree.getroot()
        
        # Check namespace
        assert 'dataPack' in root.tag
        assert 'data.xsd' in root.tag

    def test_output_contains_two_invoices(self, sample_xml_path, temp_output_dir):
        """Test that output contains both invoices from sample."""
        output_file = os.path.join(temp_output_dir, 'output.xml')
        convert_xml(sample_xml_path, output_file)
        
        tree = ET.parse(output_file)
        root = tree.getroot()
        
        # Count dataPackItem elements
        ns = {'dat': 'http://www.stormware.cz/schema/version_2/data.xsd'}
        items = root.findall('dat:dataPackItem', ns)
        assert len(items) == 2

    def test_output_preserves_invoice_ids(self, sample_xml_path, temp_output_dir):
        """Test that invoice IDs are preserved in output."""
        output_file = os.path.join(temp_output_dir, 'output.xml')
        convert_xml(sample_xml_path, output_file)
        
        tree = ET.parse(output_file)
        root = tree.getroot()
        
        ns = {
            'dat': 'http://www.stormware.cz/schema/version_2/data.xsd',
            'inv': 'http://www.stormware.cz/schema/version_2/invoice.xsd',
            'typ': 'http://www.stormware.cz/schema/version_2/type.xsd'
        }
        
        items = root.findall('dat:dataPackItem', ns)
        
        # Extract invoice IDs from numberRequested
        invoice_ids = []
        for item in items:
            num_req = item.find('.//typ:numberRequested', ns)
            if num_req is not None:
                invoice_ids.append(num_req.text)
        
        assert 'INV-001' in invoice_ids
        assert 'INV-002' in invoice_ids

    def test_output_contains_partner_info(self, sample_xml_path, temp_output_dir):
        """Test that partner information is included in output."""
        output_file = os.path.join(temp_output_dir, 'output.xml')
        convert_xml(sample_xml_path, output_file)
        
        tree = ET.parse(output_file)
        root = tree.getroot()
        
        ns = {
            'dat': 'http://www.stormware.cz/schema/version_2/data.xsd',
            'inv': 'http://www.stormware.cz/schema/version_2/invoice.xsd',
            'typ': 'http://www.stormware.cz/schema/version_2/type.xsd'
        }
        
        companies = root.findall('.//typ:company', ns)
        company_names = [c.text for c in companies]
        
        assert 'Acme Corporation' in company_names
        assert 'Beta Ltd' in company_names

    def test_output_contains_vat_rates(self, sample_xml_path, temp_output_dir):
        """Test that VAT rates are included in output."""
        output_file = os.path.join(temp_output_dir, 'output.xml')
        convert_xml(sample_xml_path, output_file)
        
        tree = ET.parse(output_file)
        root = tree.getroot()
        
        ns = {
            'inv': 'http://www.stormware.cz/schema/version_2/invoice.xsd',
        }
        
        vat_rates = root.findall('.//inv:rateVAT', ns)
        assert len(vat_rates) == 2
        
        rates = [v.text for v in vat_rates]
        assert 'high' in rates
        assert 'low' in rates


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_iso_date_with_iso_format(self):
        """Test iso_date with ISO format input."""
        result = iso_date("2024-01-15")
        assert result == "2024-01-15"

    def test_iso_date_with_czech_format(self):
        """Test iso_date with Czech format input."""
        result = iso_date("15.01.2024")
        assert result == "2024-01-15"

    def test_iso_date_with_invalid_format(self):
        """Test iso_date with invalid format returns today's date."""
        result = iso_date("invalid")
        # Should return today's date in ISO format
        assert len(result) == 10
        assert result.count('-') == 2

    def test_get_text_with_existing_element(self):
        """Test get_text with existing element."""
        root = ET.fromstring('<root><name>Test</name></root>')
        result = get_text(root, 'name')
        assert result == 'Test'

    def test_get_text_with_missing_element(self):
        """Test get_text with missing element."""
        root = ET.fromstring('<root></root>')
        result = get_text(root, 'name')
        assert result == ''

    def test_get_text_strips_whitespace(self):
        """Test get_text strips whitespace."""
        root = ET.fromstring('<root><name>  Test  </name></root>')
        result = get_text(root, 'name')
        assert result == 'Test'

    def test_detect_vat_high_price(self):
        """Test detect_vat with high price."""
        root = ET.fromstring('''
            <item>
                <price_high>1000.00</price_high>
                <price_low></price_low>
                <price_none></price_none>
            </item>
        ''')
        vat_type, price = detect_vat(root)
        assert vat_type == 'high'
        assert price == '1000.00'

    def test_detect_vat_low_price(self):
        """Test detect_vat with low price."""
        root = ET.fromstring('''
            <item>
                <price_high></price_high>
                <price_low>500.00</price_low>
                <price_none></price_none>
            </item>
        ''')
        vat_type, price = detect_vat(root)
        assert vat_type == 'low'
        assert price == '500.00'

    def test_detect_vat_no_price(self):
        """Test detect_vat with no price."""
        root = ET.fromstring('''
            <item>
                <price_high></price_high>
                <price_low></price_low>
                <price_none>0</price_none>
            </item>
        ''')
        vat_type, price = detect_vat(root)
        assert vat_type == 'none'
        assert price == '0'


class TestRounding:
    """Tests for rounding functionality (1 decimal, <=4 down, >5 up)."""

    def test_round_price_down_at_4(self):
        """Test rounding down when second decimal is 4."""
        assert round_price(100.04) == 100.0
        assert round_price(100.14) == 100.1
        assert round_price(100.44) == 100.4

    def test_round_price_up_at_5(self):
        """Test rounding up when second decimal is 5."""
        assert round_price(100.05) == 100.1
        assert round_price(100.15) == 100.2
        assert round_price(100.45) == 100.5

    def test_round_price_up_at_6_and_above(self):
        """Test rounding up when second decimal is 6 or above."""
        assert round_price(100.06) == 100.1
        assert round_price(100.17) == 100.2
        assert round_price(100.48) == 100.5
        assert round_price(100.99) == 101.0

    def test_round_price_exact_decimal(self):
        """Test that exact decimals stay unchanged."""
        assert round_price(100.0) == 100.0
        assert round_price(100.1) == 100.1
        assert round_price(100.5) == 100.5

    def test_round_price_negative(self):
        """Test rounding negative numbers."""
        assert round_price(-100.04) == -100.0
        assert round_price(-100.05) == -100.1


class TestMultipleVatRates:
    """Tests for handling invoices with multiple VAT rates."""

    def test_get_vat_items_single_high(self):
        """Test invoice with only high VAT."""
        root = ET.fromstring('''
            <item>
                <price_high>1000</price_high>
                <price_vat_high>1210</price_vat_high>
                <price_low>0</price_low>
                <price_vat_low>0</price_vat_low>
                <price_none>0</price_none>
                <price_vat_none>0</price_vat_none>
            </item>
        ''')
        items = get_vat_items(root)
        assert len(items) == 1
        assert items[0]['vat_rate'] == 'high'
        assert items[0]['base_price'] == 1000.0
        assert items[0]['price_with_vat'] == 1210.0

    def test_get_vat_items_high_and_none(self):
        """Test invoice with high VAT and no VAT items (like invoice 32600049)."""
        root = ET.fromstring('''
            <item>
                <price_high>7990.1</price_high>
                <price_vat_high>9668</price_vat_high>
                <price_low>0</price_low>
                <price_vat_low>0</price_vat_low>
                <price_none>618</price_none>
                <price_vat_none>618</price_vat_none>
            </item>
        ''')
        items = get_vat_items(root)
        assert len(items) == 2

        # Find high VAT item
        high_item = next(i for i in items if i['vat_rate'] == 'high')
        assert high_item['base_price'] == 7990.1
        assert high_item['price_with_vat'] == 9668.0

        # Find no VAT item
        none_item = next(i for i in items if i['vat_rate'] == 'none')
        assert none_item['base_price'] == 618.0
        assert none_item['price_with_vat'] == 618.0

    def test_get_vat_items_all_three_rates(self):
        """Test invoice with all three VAT rates."""
        root = ET.fromstring('''
            <item>
                <price_high>1000</price_high>
                <price_vat_high>1210</price_vat_high>
                <price_low>500</price_low>
                <price_vat_low>560</price_vat_low>
                <price_none>200</price_none>
                <price_vat_none>200</price_vat_none>
            </item>
        ''')
        items = get_vat_items(root)
        assert len(items) == 3


class TestInvoiceTotals:
    """Tests for correct invoice total calculations."""

    def test_invoice_32600049_total(self, temp_output_dir):
        """Test that invoice 32600049 total is 10286 (9668 + 618)."""
        # Create test XML with invoice 32600049 data
        test_xml = '''<?xml version="1.0" encoding="utf-8"?>
<items>
    <item>
        <invoice_id>32600049</invoice_id>
        <supplier_ico>31930086</supplier_ico>
        <date_create>2026-02-20</date_create>
        <date_delivery>2026-02-20</date_delivery>
        <date_due>2026-03-02</date_due>
        <billing_name>Test Company</billing_name>
        <billing_street>Test Street</billing_street>
        <billing_street_number>1</billing_street_number>
        <billing_town>Prague</billing_town>
        <billing_zip>11000</billing_zip>
        <billing_state>CZ</billing_state>
        <price_high>7990.1</price_high>
        <price_vat_high>9668</price_vat_high>
        <price_low>0</price_low>
        <price_vat_low>0</price_vat_low>
        <price_none>618</price_none>
        <price_vat_none>618</price_vat_none>
    </item>
</items>'''

        input_file = os.path.join(temp_output_dir, 'input.xml')
        output_file = os.path.join(temp_output_dir, 'output.xml')

        with open(input_file, 'w') as f:
            f.write(test_xml)

        convert_xml(input_file, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()

        ns = {
            'inv': 'http://www.stormware.cz/schema/version_2/invoice.xsd',
            'typ': 'http://www.stormware.cz/schema/version_2/type.xsd'
        }

        # Get all unit prices
        unit_prices = root.findall('.//typ:unitPrice', ns)
        total = sum(float(p.text) for p in unit_prices)

        # Total should be 7990.1 + 618 = 8608.1 (base prices)
        assert abs(total - 8608.1) < 0.01, f"Expected 8608.1, got {total}"

    def test_invoice_with_rounding(self, temp_output_dir):
        """Test that prices are rounded to 1 decimal correctly."""
        test_xml = '''<?xml version="1.0" encoding="utf-8"?>
<items>
    <item>
        <invoice_id>TEST001</invoice_id>
        <supplier_ico>12345678</supplier_ico>
        <date_create>2026-01-01</date_create>
        <date_delivery>2026-01-01</date_delivery>
        <date_due>2026-01-15</date_due>
        <billing_name>Test</billing_name>
        <billing_street>Test</billing_street>
        <billing_street_number>1</billing_street_number>
        <billing_town>Prague</billing_town>
        <billing_zip>11000</billing_zip>
        <billing_state>CZ</billing_state>
        <price_high>100.04</price_high>
        <price_vat_high>121.05</price_vat_high>
        <price_low>0</price_low>
        <price_vat_low>0</price_vat_low>
        <price_none>0</price_none>
        <price_vat_none>0</price_vat_none>
    </item>
</items>'''

        input_file = os.path.join(temp_output_dir, 'input.xml')
        output_file = os.path.join(temp_output_dir, 'output.xml')

        with open(input_file, 'w') as f:
            f.write(test_xml)

        convert_xml(input_file, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()

        ns = {'typ': 'http://www.stormware.cz/schema/version_2/type.xsd'}

        unit_price = root.find('.//typ:unitPrice', ns)

        # 100.04 should round to 100.0
        assert unit_price.text == '100.0', f"Expected '100.0', got '{unit_price.text}'"
