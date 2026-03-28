import pytest
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wexbo2pohoda.wexbo2pohoda import convert_xml, get_text, detect_vat, iso_date


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
