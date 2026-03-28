import pytest
import os
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wexbo2pohoda.wexbo2pohoda import (
    iso_date,
    get_text,
    detect_vat,
    load_source_xml,
    generate_output_filename,
    create_datapack_root,
    create_invoice_header,
    create_partner_identity,
    create_activity,
    create_invoice_items,
    create_invoice_element,
    write_output_xml,
    NS_DAT,
    NS_INV,
    NS_TYP,
    TEXT_POLOZKY
)


class TestIsoDate:
    """Unit tests for iso_date function."""

    def test_iso_format_unchanged(self):
        """Test that ISO format dates remain unchanged."""
        assert iso_date("2024-01-15") == "2024-01-15"
        assert iso_date("2023-12-31") == "2023-12-31"

    def test_czech_format_converted(self):
        """Test that Czech format dates are converted to ISO."""
        assert iso_date("15.01.2024") == "2024-01-15"
        assert iso_date("31.12.2023") == "2023-12-31"

    def test_invalid_format_returns_today(self):
        """Test that invalid dates return today's date."""
        result = iso_date("invalid-date")
        today = datetime.now().strftime("%Y-%m-%d")
        assert result == today

    def test_empty_string_returns_today(self):
        """Test that empty string returns today's date."""
        result = iso_date("")
        today = datetime.now().strftime("%Y-%m-%d")
        assert result == today


class TestGetText:
    """Unit tests for get_text function."""

    def test_existing_element(self):
        """Test extracting text from existing element."""
        root = ET.fromstring('<root><name>Test Value</name></root>')
        assert get_text(root, 'name') == 'Test Value'

    def test_missing_element(self):
        """Test that missing element returns empty string."""
        root = ET.fromstring('<root></root>')
        assert get_text(root, 'name') == ''

    def test_whitespace_stripped(self):
        """Test that whitespace is stripped."""
        root = ET.fromstring('<root><name>  Test  </name></root>')
        assert get_text(root, 'name') == 'Test'

    def test_empty_element(self):
        """Test that empty element returns empty string."""
        root = ET.fromstring('<root><name></name></root>')
        assert get_text(root, 'name') == ''


class TestDetectVat:
    """Unit tests for detect_vat function."""

    def test_high_vat_rate(self):
        """Test detection of high VAT rate."""
        item = ET.fromstring('''
            <item>
                <price_high>1000.00</price_high>
                <price_low></price_low>
                <price_none></price_none>
            </item>
        ''')
        vat_type, price = detect_vat(item)
        assert vat_type == 'high'
        assert price == '1000.00'

    def test_low_vat_rate(self):
        """Test detection of low VAT rate."""
        item = ET.fromstring('''
            <item>
                <price_high></price_high>
                <price_low>500.00</price_low>
                <price_none></price_none>
            </item>
        ''')
        vat_type, price = detect_vat(item)
        assert vat_type == 'low'
        assert price == '500.00'

    def test_no_vat(self):
        """Test detection when no VAT."""
        item = ET.fromstring('''
            <item>
                <price_high></price_high>
                <price_low></price_low>
                <price_none>100.00</price_none>
            </item>
        ''')
        vat_type, price = detect_vat(item)
        assert vat_type == 'none'
        assert price == '100.00'

    def test_zero_high_price_uses_low(self):
        """Test that zero high price falls through to low."""
        item = ET.fromstring('''
            <item>
                <price_high>0</price_high>
                <price_low>500.00</price_low>
                <price_none></price_none>
            </item>
        ''')
        vat_type, price = detect_vat(item)
        assert vat_type == 'low'
        assert price == '500.00'

    def test_all_empty_returns_zero(self):
        """Test that all empty prices returns none with 0."""
        item = ET.fromstring('''
            <item>
                <price_high></price_high>
                <price_low></price_low>
                <price_none></price_none>
            </item>
        ''')
        vat_type, price = detect_vat(item)
        assert vat_type == 'none'
        assert price == '0'


class TestLoadSourceXml:
    """Unit tests for load_source_xml function."""

    @pytest.fixture
    def sample_xml_file(self):
        """Create a temporary XML file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write('''<?xml version="1.0"?>
                <root>
                    <item><id>1</id></item>
                    <item><id>2</id></item>
                </root>
            ''')
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)

    def test_load_valid_xml(self, sample_xml_file):
        """Test loading valid XML file."""
        orders = load_source_xml(sample_xml_file)
        assert len(orders) == 2
        assert orders[0].find('id').text == '1'
        assert orders[1].find('id').text == '2'

    def test_load_nonexistent_file(self):
        """Test that loading nonexistent file raises exception."""
        with pytest.raises(Exception):
            load_source_xml('/nonexistent/file.xml')

    def test_load_invalid_xml(self):
        """Test that loading invalid XML raises exception."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write('invalid xml content')
            temp_path = f.name
        
        try:
            with pytest.raises(Exception):
                load_source_xml(temp_path)
        finally:
            os.unlink(temp_path)


class TestGenerateOutputFilename:
    """Unit tests for generate_output_filename function."""

    def test_generates_filename_in_same_directory(self):
        """Test that output file is in same directory as input."""
        input_file = '/path/to/input.xml'
        output = generate_output_filename(input_file)
        assert os.path.dirname(output) == '/path/to'

    def test_filename_contains_timestamp(self):
        """Test that filename contains timestamp."""
        input_file = '/path/to/input.xml'
        output = generate_output_filename(input_file)
        assert 'pohoda_import_' in output
        assert output.endswith('.xml')

    def test_filename_format(self):
        """Test filename format matches expected pattern."""
        input_file = '/path/to/input.xml'
        output = generate_output_filename(input_file)
        filename = os.path.basename(output)
        assert filename.startswith('pohoda_import_')
        assert len(filename) == len('pohoda_import_YYYYMMDD_HHMMSS.xml')


class TestCreateDatapackRoot:
    """Unit tests for create_datapack_root function."""

    def test_creates_element_with_correct_tag(self):
        """Test that element has correct tag."""
        datapack = create_datapack_root('12345678')
        assert 'dataPack' in datapack.tag
        assert NS_DAT in datapack.tag

    def test_sets_ico_attribute(self):
        """Test that ICO attribute is set correctly."""
        datapack = create_datapack_root('12345678')
        assert datapack.get('ico') == '12345678'

    def test_sets_all_required_attributes(self):
        """Test that all required attributes are set."""
        datapack = create_datapack_root('12345678')
        assert datapack.get('id') == 'WEXBO'
        assert datapack.get('application') == 'Wexbo import'
        assert datapack.get('version') == '2.0'
        assert datapack.get('note') == 'Import faktur z e-shopu'


class TestCreateInvoiceHeader:
    """Unit tests for create_invoice_header function."""

    @pytest.fixture
    def order_element(self):
        """Create sample order element."""
        return ET.fromstring('''
            <item>
                <invoice_id>INV-001</invoice_id>
                <date_create>2024-01-15</date_create>
                <date_delivery>2024-01-15</date_delivery>
                <date_due>2024-02-15</date_due>
            </item>
        ''')

    def test_creates_invoice_type(self, order_element):
        """Test that invoice type is created."""
        header = ET.Element('header')
        create_invoice_header(header, order_element)
        
        inv_type = header.find(f'.//{{{NS_INV}}}invoiceType')
        assert inv_type is not None
        assert inv_type.text == 'issuedInvoice'

    def test_creates_invoice_number(self, order_element):
        """Test that invoice number is created."""
        header = ET.Element('header')
        create_invoice_header(header, order_element)
        
        num_req = header.find(f'.//{{{NS_TYP}}}numberRequested')
        assert num_req is not None
        assert num_req.text == 'INV-001'

    def test_creates_dates(self, order_element):
        """Test that all dates are created."""
        header = ET.Element('header')
        create_invoice_header(header, order_element)
        
        date = header.find(f'.//{{{NS_INV}}}date')
        date_tax = header.find(f'.//{{{NS_INV}}}dateTax')
        date_due = header.find(f'.//{{{NS_INV}}}dateDue')
        
        assert date is not None
        assert date_tax is not None
        assert date_due is not None


class TestCreatePartnerIdentity:
    """Unit tests for create_partner_identity function."""

    @pytest.fixture
    def order_element(self):
        """Create sample order element."""
        return ET.fromstring('''
            <item>
                <billing_name>Acme Corp</billing_name>
                <billing_street>Main St</billing_street>
                <billing_street_number>123</billing_street_number>
                <billing_town>Prague</billing_town>
                <billing_zip>11000</billing_zip>
                <billing_state>CZ</billing_state>
            </item>
        ''')

    def test_creates_company_name(self, order_element):
        """Test that company name is created."""
        header = ET.Element('header')
        create_partner_identity(header, order_element)
        
        company = header.find(f'.//{{{NS_TYP}}}company')
        assert company is not None
        assert company.text == 'Acme Corp'

    def test_creates_street_address(self, order_element):
        """Test that street address is created."""
        header = ET.Element('header')
        create_partner_identity(header, order_element)
        
        street = header.find(f'.//{{{NS_TYP}}}street')
        assert street is not None
        assert street.text == 'Main St 123'

    def test_creates_city_and_zip(self, order_element):
        """Test that city and zip are created."""
        header = ET.Element('header')
        create_partner_identity(header, order_element)
        
        city = header.find(f'.//{{{NS_TYP}}}city')
        zip_code = header.find(f'.//{{{NS_TYP}}}zip')
        
        assert city is not None
        assert city.text == 'Prague'
        assert zip_code is not None
        assert zip_code.text == '11000'

    def test_creates_country_when_present(self, order_element):
        """Test that country is created when present."""
        header = ET.Element('header')
        create_partner_identity(header, order_element)
        
        country_ids = header.find(f'.//{{{NS_TYP}}}country/{{{NS_TYP}}}ids')
        assert country_ids is not None
        assert country_ids.text == 'CZ'

    def test_no_country_when_empty(self):
        """Test that country is not created when empty."""
        order = ET.fromstring('''
            <item>
                <billing_name>Acme Corp</billing_name>
                <billing_street>Main St</billing_street>
                <billing_street_number>123</billing_street_number>
                <billing_town>Prague</billing_town>
                <billing_zip>11000</billing_zip>
                <billing_state></billing_state>
            </item>
        ''')
        header = ET.Element('header')
        create_partner_identity(header, order)
        
        country = header.find(f'.//{{{NS_TYP}}}country')
        assert country is None


class TestCreateActivity:
    """Unit tests for create_activity function."""

    def test_creates_activity_element(self):
        """Test that activity element is created."""
        header = ET.Element('header')
        create_activity(header)
        
        activity_ids = header.find(f'.//{{{NS_INV}}}activity/{{{NS_TYP}}}ids')
        assert activity_ids is not None
        assert activity_ids.text == 'Pom'


class TestCreateInvoiceItems:
    """Unit tests for create_invoice_items function."""

    @pytest.fixture
    def order_element(self):
        """Create sample order element."""
        return ET.fromstring('''
            <item>
                <price_high>1000.00</price_high>
                <price_low></price_low>
                <price_none></price_none>
            </item>
        ''')

    def test_creates_item_text(self, order_element):
        """Test that item text is created."""
        invoice = ET.Element('invoice')
        create_invoice_items(invoice, order_element)
        
        text = invoice.find(f'.//{{{NS_INV}}}invoiceItem/{{{NS_INV}}}text')
        assert text is not None
        assert text.text == TEXT_POLOZKY

    def test_creates_quantity_and_unit(self, order_element):
        """Test that quantity and unit are created."""
        invoice = ET.Element('invoice')
        create_invoice_items(invoice, order_element)
        
        quantity = invoice.find(f'.//{{{NS_INV}}}quantity')
        unit = invoice.find(f'.//{{{NS_INV}}}unit')
        
        assert quantity is not None
        assert quantity.text == '1'
        assert unit is not None
        assert unit.text == 'ks'

    def test_creates_vat_rate(self, order_element):
        """Test that VAT rate is created."""
        invoice = ET.Element('invoice')
        create_invoice_items(invoice, order_element)
        
        vat_rate = invoice.find(f'.//{{{NS_INV}}}rateVAT')
        assert vat_rate is not None
        assert vat_rate.text == 'high'

    def test_creates_unit_price(self, order_element):
        """Test that unit price is created."""
        invoice = ET.Element('invoice')
        create_invoice_items(invoice, order_element)
        
        unit_price = invoice.find(f'.//{{{NS_INV}}}homeCurrency/{{{NS_TYP}}}unitPrice')
        assert unit_price is not None
        assert unit_price.text == '1000.00'


class TestCreateInvoiceElement:
    """Unit tests for create_invoice_element function."""

    @pytest.fixture
    def order_element(self):
        """Create sample order element."""
        return ET.fromstring('''
            <item>
                <invoice_id>INV-001</invoice_id>
                <date_create>2024-01-15</date_create>
                <date_delivery>2024-01-15</date_delivery>
                <date_due>2024-02-15</date_due>
                <billing_name>Acme Corp</billing_name>
                <billing_street>Main St</billing_street>
                <billing_street_number>123</billing_street_number>
                <billing_town>Prague</billing_town>
                <billing_zip>11000</billing_zip>
                <billing_state>CZ</billing_state>
                <price_high>1000.00</price_high>
                <price_low></price_low>
                <price_none></price_none>
            </item>
        ''')

    def test_creates_datapack_item(self, order_element):
        """Test that dataPackItem is created."""
        datapack = ET.Element('datapack')
        create_invoice_element(datapack, order_element, 1)
        
        pack_item = datapack.find(f'.//{{{NS_DAT}}}dataPackItem')
        assert pack_item is not None
        assert pack_item.get('id') == '1'
        assert pack_item.get('version') == '2.0'

    def test_creates_invoice(self, order_element):
        """Test that invoice is created."""
        datapack = ET.Element('datapack')
        invoice = create_invoice_element(datapack, order_element, 1)
        
        assert invoice is not None
        assert 'invoice' in invoice.tag

    def test_creates_complete_structure(self, order_element):
        """Test that complete invoice structure is created."""
        datapack = ET.Element('datapack')
        create_invoice_element(datapack, order_element, 1)
        
        header = datapack.find(f'.//{{{NS_INV}}}invoiceHeader')
        partner = datapack.find(f'.//{{{NS_INV}}}partnerIdentity')
        activity = datapack.find(f'.//{{{NS_INV}}}activity')
        detail = datapack.find(f'.//{{{NS_INV}}}invoiceDetail')
        
        assert header is not None
        assert partner is not None
        assert activity is not None
        assert detail is not None


class TestWriteOutputXml:
    """Unit tests for write_output_xml function."""

    def test_writes_file(self):
        """Test that file is written."""
        datapack = ET.Element('datapack')
        ET.SubElement(datapack, 'test').text = 'value'
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as f:
            temp_path = f.name
        
        try:
            write_output_xml(datapack, temp_path)
            assert os.path.exists(temp_path)
            
            tree = ET.parse(temp_path)
            root = tree.getroot()
            assert root.tag == 'datapack'
        finally:
            os.unlink(temp_path)

    def test_writes_valid_xml(self):
        """Test that written file is valid XML."""
        datapack = ET.Element('datapack')
        ET.SubElement(datapack, 'test').text = 'value'
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as f:
            temp_path = f.name
        
        try:
            write_output_xml(datapack, temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
                assert content.startswith('<?xml version')
        finally:
            os.unlink(temp_path)

    def test_raises_on_invalid_path(self):
        """Test that exception is raised for invalid path."""
        datapack = ET.Element('datapack')
        
        with pytest.raises(Exception):
            write_output_xml(datapack, '/nonexistent/directory/file.xml')
