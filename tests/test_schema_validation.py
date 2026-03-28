import pytest
import os
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wexbo2pohoda.wexbo2pohoda import convert_xml, NS_DAT, NS_INV, NS_TYP

try:
    from lxml import etree
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False


@pytest.fixture
def sample_xml_path():
    """Return path to sample XML fixture."""
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_export.xml')


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestSchemaValidation:
    """Tests to validate output XML against Pohoda XML schemas."""

    @pytest.fixture
    def output_xml(self, sample_xml_path, temp_output_dir):
        """Generate output XML for testing."""
        output_file = os.path.join(temp_output_dir, 'output.xml')
        convert_xml(sample_xml_path, output_file)
        return output_file

    def test_output_has_datapck_root_element(self, output_xml):
        """Test that output has dataPack as root element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        assert 'dataPack' in root.tag
        assert NS_DAT in root.tag

    def test_datapck_has_required_attributes(self, output_xml):
        """Test that dataPack has all required attributes."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        required_attrs = ['id', 'ico', 'application', 'version']
        for attr in required_attrs:
            assert root.get(attr) is not None, f"Missing required attribute: {attr}"

    def test_datapck_version_is_2_0(self, output_xml):
        """Test that dataPack version is 2.0."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        assert root.get('version') == '2.0'

    def test_datapck_has_datapackitems(self, output_xml):
        """Test that dataPack contains dataPackItem elements."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'dat': NS_DAT}
        items = root.findall('dat:dataPackItem', ns)
        assert len(items) > 0, "dataPack must contain at least one dataPackItem"

    def test_each_datapackitem_has_required_attributes(self, output_xml):
        """Test that each dataPackItem has required attributes."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'dat': NS_DAT}
        items = root.findall('dat:dataPackItem', ns)
        
        for item in items:
            assert item.get('id') is not None, "dataPackItem must have id attribute"
            assert item.get('version') is not None, "dataPackItem must have version attribute"
            assert item.get('version') == '2.0', "dataPackItem version must be 2.0"

    def test_each_datapackitem_has_invoice(self, output_xml):
        """Test that each dataPackItem contains an invoice element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'dat': NS_DAT, 'inv': NS_INV}
        items = root.findall('dat:dataPackItem', ns)
        
        for item in items:
            invoice = item.find('inv:invoice', ns)
            assert invoice is not None, "dataPackItem must contain an invoice element"

    def test_each_invoice_has_required_attributes(self, output_xml):
        """Test that each invoice has required attributes."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        invoices = root.findall('.//inv:invoice', ns)
        
        for invoice in invoices:
            assert invoice.get('version') is not None, "invoice must have version attribute"
            assert invoice.get('version') == '2.0', "invoice version must be 2.0"

    def test_each_invoice_has_invoiceheader(self, output_xml):
        """Test that each invoice contains invoiceHeader element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        invoices = root.findall('.//inv:invoice', ns)
        
        for invoice in invoices:
            header = invoice.find('inv:invoiceHeader', ns)
            assert header is not None, "invoice must contain invoiceHeader element"

    def test_invoiceheader_has_invoicetype(self, output_xml):
        """Test that invoiceHeader contains invoiceType element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        headers = root.findall('.//inv:invoiceHeader', ns)
        
        for header in headers:
            inv_type = header.find('inv:invoiceType', ns)
            assert inv_type is not None, "invoiceHeader must contain invoiceType element"
            assert inv_type.text in ['issuedInvoice', 'receivedInvoice'], \
                f"invoiceType must be 'issuedInvoice' or 'receivedInvoice', got {inv_type.text}"

    def test_invoiceheader_has_number_element(self, output_xml):
        """Test that invoiceHeader contains number element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        headers = root.findall('.//inv:invoiceHeader', ns)
        
        for header in headers:
            number = header.find('inv:number', ns)
            assert number is not None, "invoiceHeader must contain number element"

    def test_number_has_numberrequested(self, output_xml):
        """Test that number element contains numberRequested."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV, 'typ': NS_TYP}
        numbers = root.findall('.//inv:number', ns)
        
        for number in numbers:
            num_req = number.find('typ:numberRequested', ns)
            assert num_req is not None, "number element must contain numberRequested"
            assert num_req.text is not None and num_req.text.strip(), \
                "numberRequested must have non-empty text"

    def test_invoiceheader_has_text_element(self, output_xml):
        """Test that invoiceHeader contains text element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        headers = root.findall('.//inv:invoiceHeader', ns)
        
        for header in headers:
            text = header.find('inv:text', ns)
            assert text is not None, "invoiceHeader must contain text element"
            assert text.text is not None and text.text.strip(), \
                "text element must have non-empty content"

    def test_invoiceheader_has_date(self, output_xml):
        """Test that invoiceHeader contains date element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        headers = root.findall('.//inv:invoiceHeader', ns)
        
        for header in headers:
            date = header.find('inv:date', ns)
            assert date is not None, "invoiceHeader must contain date element"
            assert date.text is not None and date.text.strip(), \
                "date element must have non-empty content"
            assert len(date.text.strip()) == 10, \
                f"date must be in ISO format (YYYY-MM-DD), got {date.text}"

    def test_invoiceheader_has_datetax(self, output_xml):
        """Test that invoiceHeader contains dateTax element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        headers = root.findall('.//inv:invoiceHeader', ns)
        
        for header in headers:
            date_tax = header.find('inv:dateTax', ns)
            assert date_tax is not None, "invoiceHeader must contain dateTax element"
            assert date_tax.text is not None and date_tax.text.strip(), \
                "dateTax element must have non-empty content"

    def test_invoiceheader_has_datedue(self, output_xml):
        """Test that invoiceHeader contains dateDue element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        headers = root.findall('.//inv:invoiceHeader', ns)
        
        for header in headers:
            date_due = header.find('inv:dateDue', ns)
            assert date_due is not None, "invoiceHeader must contain dateDue element"
            assert date_due.text is not None and date_due.text.strip(), \
                "dateDue element must have non-empty content"

    def test_invoiceheader_has_partneridentity(self, output_xml):
        """Test that invoiceHeader contains partnerIdentity element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        headers = root.findall('.//inv:invoiceHeader', ns)
        
        for header in headers:
            partner = header.find('inv:partnerIdentity', ns)
            assert partner is not None, "invoiceHeader must contain partnerIdentity element"

    def test_partneridentity_has_address(self, output_xml):
        """Test that partnerIdentity contains address element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV, 'typ': NS_TYP}
        partners = root.findall('.//inv:partnerIdentity', ns)
        
        for partner in partners:
            address = partner.find('typ:address', ns)
            assert address is not None, "partnerIdentity must contain address element"

    def test_address_has_company(self, output_xml):
        """Test that address contains company element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'typ': NS_TYP}
        addresses = root.findall('.//typ:address', ns)
        
        for address in addresses:
            company = address.find('typ:company', ns)
            assert company is not None, "address must contain company element"
            assert company.text is not None and company.text.strip(), \
                "company element must have non-empty content"

    def test_address_has_street(self, output_xml):
        """Test that address contains street element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'typ': NS_TYP}
        addresses = root.findall('.//typ:address', ns)
        
        for address in addresses:
            street = address.find('typ:street', ns)
            assert street is not None, "address must contain street element"
            assert street.text is not None and street.text.strip(), \
                "street element must have non-empty content"

    def test_address_has_city(self, output_xml):
        """Test that address contains city element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'typ': NS_TYP}
        addresses = root.findall('.//typ:address', ns)
        
        for address in addresses:
            city = address.find('typ:city', ns)
            assert city is not None, "address must contain city element"
            assert city.text is not None and city.text.strip(), \
                "city element must have non-empty content"

    def test_address_has_zip(self, output_xml):
        """Test that address contains zip element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'typ': NS_TYP}
        addresses = root.findall('.//typ:address', ns)
        
        for address in addresses:
            zip_code = address.find('typ:zip', ns)
            assert zip_code is not None, "address must contain zip element"
            assert zip_code.text is not None and zip_code.text.strip(), \
                "zip element must have non-empty content"

    def test_invoiceheader_has_activity(self, output_xml):
        """Test that invoiceHeader contains activity element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        headers = root.findall('.//inv:invoiceHeader', ns)
        
        for header in headers:
            activity = header.find('inv:activity', ns)
            assert activity is not None, "invoiceHeader must contain activity element"

    def test_activity_has_ids(self, output_xml):
        """Test that activity contains ids element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV, 'typ': NS_TYP}
        activities = root.findall('.//inv:activity', ns)
        
        for activity in activities:
            ids = activity.find('typ:ids', ns)
            assert ids is not None, "activity must contain ids element"
            assert ids.text is not None and ids.text.strip(), \
                "activity ids element must have non-empty content"

    def test_invoice_has_invoicedetail(self, output_xml):
        """Test that invoice contains invoiceDetail element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        invoices = root.findall('.//inv:invoice', ns)
        
        for invoice in invoices:
            detail = invoice.find('inv:invoiceDetail', ns)
            assert detail is not None, "invoice must contain invoiceDetail element"

    def test_invoicedetail_has_invoiceitems(self, output_xml):
        """Test that invoiceDetail contains invoiceItem elements."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        details = root.findall('.//inv:invoiceDetail', ns)
        
        for detail in details:
            items = detail.findall('inv:invoiceItem', ns)
            assert len(items) > 0, "invoiceDetail must contain at least one invoiceItem"

    def test_invoiceitem_has_text(self, output_xml):
        """Test that invoiceItem contains text element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        items = root.findall('.//inv:invoiceItem', ns)
        
        for item in items:
            text = item.find('inv:text', ns)
            assert text is not None, "invoiceItem must contain text element"
            assert text.text is not None and text.text.strip(), \
                "invoiceItem text element must have non-empty content"

    def test_invoiceitem_has_quantity(self, output_xml):
        """Test that invoiceItem contains quantity element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        items = root.findall('.//inv:invoiceItem', ns)
        
        for item in items:
            quantity = item.find('inv:quantity', ns)
            assert quantity is not None, "invoiceItem must contain quantity element"
            assert quantity.text is not None and quantity.text.strip(), \
                "invoiceItem quantity element must have non-empty content"

    def test_invoiceitem_has_unit(self, output_xml):
        """Test that invoiceItem contains unit element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        items = root.findall('.//inv:invoiceItem', ns)
        
        for item in items:
            unit = item.find('inv:unit', ns)
            assert unit is not None, "invoiceItem must contain unit element"
            assert unit.text is not None and unit.text.strip(), \
                "invoiceItem unit element must have non-empty content"

    def test_invoiceitem_has_ratevat(self, output_xml):
        """Test that invoiceItem contains rateVAT element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        items = root.findall('.//inv:invoiceItem', ns)
        
        for item in items:
            rate_vat = item.find('inv:rateVAT', ns)
            assert rate_vat is not None, "invoiceItem must contain rateVAT element"
            assert rate_vat.text in ['high', 'low', 'none'], \
                f"rateVAT must be 'high', 'low', or 'none', got {rate_vat.text}"

    def test_invoiceitem_has_homecurrency(self, output_xml):
        """Test that invoiceItem contains homeCurrency element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        items = root.findall('.//inv:invoiceItem', ns)
        
        for item in items:
            home_curr = item.find('inv:homeCurrency', ns)
            assert home_curr is not None, "invoiceItem must contain homeCurrency element"

    def test_item_homecurrency_has_unitprice(self, output_xml):
        """Test that item homeCurrency contains unitPrice element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV, 'typ': NS_TYP}
        items = root.findall('.//inv:invoiceItem', ns)
        
        for item in items:
            home_curr = item.find('inv:homeCurrency', ns)
            unit_price = home_curr.find('typ:unitPrice', ns)
            assert unit_price is not None, "item homeCurrency must contain unitPrice element"
            assert unit_price.text is not None and unit_price.text.strip(), \
                "unitPrice element must have non-empty content"

    def test_item_homecurrency_has_price_and_pricevat(self, output_xml):
        """Test that item homeCurrency contains price and priceVAT elements."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV, 'typ': NS_TYP}
        items = root.findall('.//inv:invoiceItem', ns)
        
        for item in items:
            home_curr = item.find('inv:homeCurrency', ns)
            price = home_curr.find('typ:price', ns)
            price_vat = home_curr.find('typ:priceVAT', ns)
            assert price is not None, "item homeCurrency must contain price element"
            assert price_vat is not None, "item homeCurrency must contain priceVAT element"

    def test_prices_are_numeric(self, output_xml):
        """Test that all prices are valid numeric values."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'typ': NS_TYP}
        unit_prices = root.findall('.//typ:unitPrice', ns)
        price_sums = root.findall('.//typ:priceSum', ns)
        
        for price in unit_prices + price_sums:
            try:
                float(price.text)
            except (ValueError, TypeError):
                pytest.fail(f"Price value '{price.text}' is not numeric")

    def test_no_extra_elements_in_datapck(self, output_xml):
        """Test that dataPack contains only dataPackItem children."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'dat': NS_DAT}
        for child in root:
            assert 'dataPackItem' in child.tag, \
                f"dataPack should only contain dataPackItem elements, found {child.tag}"

    def test_no_extra_elements_in_datapackitem(self, output_xml):
        """Test that dataPackItem contains only invoice child."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'dat': NS_DAT, 'inv': NS_INV}
        items = root.findall('dat:dataPackItem', ns)
        
        for item in items:
            for child in item:
                assert 'invoice' in child.tag, \
                    f"dataPackItem should only contain invoice element, found {child.tag}"

    def test_no_extra_elements_in_invoice(self, output_xml):
        """Test that invoice contains only invoiceHeader and invoiceDetail."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        invoices = root.findall('.//inv:invoice', ns)
        
        allowed_tags = {'invoiceHeader', 'invoiceDetail', 'invoiceSummary'}
        for invoice in invoices:
            for child in invoice:
                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                assert tag_name in allowed_tags, \
                    f"invoice should only contain invoiceHeader, invoiceDetail, and invoiceSummary, found {tag_name}"

    def test_no_extra_elements_in_invoiceheader(self, output_xml):
        """Test that invoiceHeader contains only expected elements."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        headers = root.findall('.//inv:invoiceHeader', ns)
        
        allowed_tags = {'invoiceType', 'number', 'text', 'date', 'dateTax', 'dateDue', 
                       'partnerIdentity', 'activity'}
        for header in headers:
            for child in header:
                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                assert tag_name in allowed_tags, \
                    f"invoiceHeader contains unexpected element: {tag_name}"

    def test_no_extra_elements_in_invoiceitem(self, output_xml):
        """Test that invoiceItem contains only expected elements."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        items = root.findall('.//inv:invoiceItem', ns)
        
        allowed_tags = {'text', 'quantity', 'unit', 'payVAT', 'rateVAT', 'homeCurrency'}
        for item in items:
            for child in item:
                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                assert tag_name in allowed_tags, \
                    f"invoiceItem contains unexpected element: {tag_name}"

    def test_no_extra_elements_in_item_homecurrency(self, output_xml):
        """Test that item homeCurrency contains only expected elements."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV, 'typ': NS_TYP}
        items = root.findall('.//inv:invoiceItem', ns)
        
        allowed_tags = {'unitPrice', 'price', 'priceVAT'}
        for item in items:
            home_curr = item.find('inv:homeCurrency', ns)
            for child in home_curr:
                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                assert tag_name in allowed_tags, \
                    f"item homeCurrency contains unexpected element: {tag_name}"

    def test_invoice_has_summary(self, output_xml):
        """Test that invoice contains invoiceSummary element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        invoices = root.findall('.//inv:invoice', ns)
        
        for invoice in invoices:
            summary = invoice.find('inv:invoiceSummary', ns)
            assert summary is not None, "invoice must contain invoiceSummary element"

    def test_summary_has_rounding_settings(self, output_xml):
        """Test that invoiceSummary has rounding settings."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        summaries = root.findall('.//inv:invoiceSummary', ns)
        
        for summary in summaries:
            rounding_doc = summary.find('inv:roundingDocument', ns)
            rounding_vat = summary.find('inv:roundingVAT', ns)
            assert rounding_doc is not None, "invoiceSummary must contain roundingDocument"
            assert rounding_vat is not None, "invoiceSummary must contain roundingVAT"

    def test_summary_has_homecurrency(self, output_xml):
        """Test that invoiceSummary has homeCurrency element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        summaries = root.findall('.//inv:invoiceSummary', ns)
        
        for summary in summaries:
            home_curr = summary.find('inv:homeCurrency', ns)
            assert home_curr is not None, "invoiceSummary must contain homeCurrency"

    def test_no_extra_elements_in_address(self, output_xml):
        """Test that address contains only expected elements."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'typ': NS_TYP}
        addresses = root.findall('.//typ:address', ns)
        
        allowed_tags = {'company', 'street', 'city', 'zip', 'country'}
        for address in addresses:
            for child in address:
                tag_name = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                assert tag_name in allowed_tags, \
                    f"address contains unexpected element: {tag_name}"

    def test_no_extra_elements_in_invoicedetail(self, output_xml):
        """Test that invoiceDetail contains only invoiceItem elements."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        details = root.findall('.//inv:invoiceDetail', ns)
        
        for detail in details:
            for child in detail:
                assert 'invoiceItem' in child.tag, \
                    f"invoiceDetail should only contain invoiceItem elements, found {child.tag}"

    def test_no_extra_elements_in_number(self, output_xml):
        """Test that number contains only numberRequested."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        numbers = root.findall('.//inv:number', ns)
        
        for number in numbers:
            for child in number:
                assert 'numberRequested' in child.tag, \
                    f"number should only contain numberRequested, found {child.tag}"

    def test_no_extra_elements_in_activity(self, output_xml):
        """Test that activity contains only ids element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        activities = root.findall('.//inv:activity', ns)
        
        for activity in activities:
            for child in activity:
                assert 'ids' in child.tag, \
                    f"activity should only contain ids element, found {child.tag}"

    def test_no_extra_elements_in_partneridentity(self, output_xml):
        """Test that partnerIdentity contains only address element."""
        tree = ET.parse(output_xml)
        root = tree.getroot()
        
        ns = {'inv': NS_INV}
        partners = root.findall('.//inv:partnerIdentity', ns)
        
        for partner in partners:
            for child in partner:
                assert 'address' in child.tag, \
                    f"partnerIdentity should only contain address element, found {child.tag}"
