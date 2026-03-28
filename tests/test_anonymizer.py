import unittest
import os
import tempfile
import xml.etree.ElementTree as ET
from src.wexbo2pohoda.anonymizer import XMLAnonymizer


class TestXMLAnonymizer(unittest.TestCase):
    """Test suite for XMLAnonymizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.anonymizer = XMLAnonymizer(seed=42)
        self.sample_xml = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <invoice_id>INV-001</invoice_id>
    <supplier_ico>12345678</supplier_ico>
    <date_create>2024-01-15</date_create>
    <date_delivery>2024-01-15</date_delivery>
    <date_due>2024-02-15</date_due>
    <billing_name>Acme Corporation</billing_name>
    <billing_street>Main Street</billing_street>
    <billing_street_number>123</billing_street_number>
    <billing_town>Prague</billing_town>
    <billing_zip>11000</billing_zip>
    <billing_state>CZ</billing_state>
    <price_high>1000.00</price_high>
    <price_low></price_low>
    <price_none></price_none>
  </item>
  <item>
    <invoice_id>INV-002</invoice_id>
    <supplier_ico>12345678</supplier_ico>
    <date_create>2024-01-20</date_create>
    <date_delivery>2024-01-20</date_delivery>
    <date_due>2024-02-20</date_due>
    <billing_name>Beta Ltd</billing_name>
    <billing_street>Secondary Ave</billing_street>
    <billing_street_number>456</billing_street_number>
    <billing_town>Brno</billing_town>
    <billing_zip>61200</billing_zip>
    <billing_state>CZ</billing_state>
    <price_high></price_high>
    <price_low>500.00</price_low>
    <price_none></price_none>
  </item>
</root>"""
    
    def test_anonymize_string_basic(self):
        """Test basic anonymization from string."""
        result = self.anonymizer.anonymize_string(self.sample_xml)
        root = ET.fromstring(result)
        
        items = root.findall('item')
        self.assertEqual(len(items), 2)
        
        first_item = items[0]
        self.assertNotEqual(first_item.find('billing_name').text, 'Acme Corporation')
        self.assertNotEqual(first_item.find('billing_street').text, 'Main Street')
        self.assertNotEqual(first_item.find('billing_town').text, 'Prague')
        self.assertNotEqual(first_item.find('billing_zip').text, '11000')
    
    def test_anonymize_preserves_structure(self):
        """Test that anonymization preserves XML structure."""
        result = self.anonymizer.anonymize_string(self.sample_xml)
        root = ET.fromstring(result)
        
        items = root.findall('item')
        first_item = items[0]
        
        self.assertIsNotNone(first_item.find('invoice_id'))
        self.assertIsNotNone(first_item.find('supplier_ico'))
        self.assertIsNotNone(first_item.find('date_create'))
        self.assertIsNotNone(first_item.find('billing_name'))
        self.assertIsNotNone(first_item.find('billing_street'))
        self.assertIsNotNone(first_item.find('billing_town'))
        self.assertIsNotNone(first_item.find('billing_zip'))
    
    def test_anonymize_preserves_non_anonymized_fields(self):
        """Test that non-anonymized fields are preserved."""
        result = self.anonymizer.anonymize_string(self.sample_xml)
        root = ET.fromstring(result)
        
        items = root.findall('item')
        first_item = items[0]
        
        self.assertEqual(first_item.find('invoice_id').text, 'INV-001')
        self.assertEqual(first_item.find('date_create').text, '2024-01-15')
        self.assertEqual(first_item.find('price_high').text, '1000.00')
        self.assertNotEqual(first_item.find('supplier_ico').text, '12345678')
    
    def test_anonymize_consistency_same_name(self):
        """Test that same names are anonymized consistently."""
        xml_with_duplicates = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Acme Corporation</billing_name>
    <billing_street>Main Street</billing_street>
    <billing_town>Prague</billing_town>
    <billing_zip>11000</billing_zip>
  </item>
  <item>
    <billing_name>Acme Corporation</billing_name>
    <billing_street>Secondary Ave</billing_street>
    <billing_town>Brno</billing_town>
    <billing_zip>61200</billing_zip>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_with_duplicates)
        root = ET.fromstring(result)
        items = root.findall('item')
        
        first_name = items[0].find('billing_name').text
        second_name = items[1].find('billing_name').text
        
        self.assertEqual(first_name, second_name)
    
    def test_anonymize_consistency_same_address(self):
        """Test that same addresses are anonymized consistently."""
        xml_with_duplicates = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Company A</billing_name>
    <billing_street>Main Street</billing_street>
    <billing_town>Prague</billing_town>
    <billing_zip>11000</billing_zip>
  </item>
  <item>
    <billing_name>Company B</billing_name>
    <billing_street>Main Street</billing_street>
    <billing_town>Prague</billing_town>
    <billing_zip>11000</billing_zip>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_with_duplicates)
        root = ET.fromstring(result)
        items = root.findall('item')
        
        first_street = items[0].find('billing_street').text
        second_street = items[1].find('billing_street').text
        self.assertEqual(first_street, second_street)
        
        first_city = items[0].find('billing_town').text
        second_city = items[1].find('billing_town').text
        self.assertEqual(first_city, second_city)
        
        first_zip = items[0].find('billing_zip').text
        second_zip = items[1].find('billing_zip').text
        self.assertEqual(first_zip, second_zip)
    
    def test_anonymize_file(self):
        """Test anonymization of actual file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, 'input.xml')
            output_file = os.path.join(tmpdir, 'output.xml')
            
            with open(input_file, 'w') as f:
                f.write(self.sample_xml)
            
            result = self.anonymizer.anonymize_file(input_file, output_file)
            
            self.assertEqual(result, output_file)
            self.assertTrue(os.path.exists(output_file))
            
            tree = ET.parse(output_file)
            root = tree.getroot()
            items = root.findall('item')
            
            self.assertEqual(len(items), 2)
            self.assertNotEqual(items[0].find('billing_name').text, 'Acme Corporation')
    
    def test_anonymize_file_auto_output_name(self):
        """Test that output file is auto-generated if not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, 'input.xml')
            
            with open(input_file, 'w') as f:
                f.write(self.sample_xml)
            
            result = self.anonymizer.anonymize_file(input_file)
            
            self.assertTrue(os.path.exists(result))
            self.assertIn('anonymized_', result)
            self.assertTrue(result.endswith('.xml'))
    
    def test_empty_fields_preserved(self):
        """Test that empty fields remain empty after anonymization."""
        xml_with_empty = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Company A</billing_name>
    <billing_street></billing_street>
    <billing_town>Prague</billing_town>
    <billing_zip></billing_zip>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_with_empty)
        root = ET.fromstring(result)
        item = root.find('item')
        
        self.assertIn(item.find('billing_street').text, ('', None))
        self.assertIn(item.find('billing_zip').text, ('', None))
    
    def test_reproducible_with_seed(self):
        """Test that same seed produces same anonymization."""
        anon1 = XMLAnonymizer(seed=123)
        result1 = anon1.anonymize_string(self.sample_xml)
        
        anon2 = XMLAnonymizer(seed=123)
        result2 = anon2.anonymize_string(self.sample_xml)
        
        root1 = ET.fromstring(result1)
        root2 = ET.fromstring(result2)
        
        items1 = root1.findall('item')
        items2 = root2.findall('item')
        
        self.assertEqual(items1[0].find('billing_name').text, items2[0].find('billing_name').text)
        self.assertEqual(items1[0].find('billing_street').text, items2[0].find('billing_street').text)
    
    def test_different_seed_produces_different_results(self):
        """Test that different seeds produce different anonymization."""
        anon1 = XMLAnonymizer(seed=123)
        result1 = anon1.anonymize_string(self.sample_xml)
        
        anon2 = XMLAnonymizer(seed=456)
        result2 = anon2.anonymize_string(self.sample_xml)
        
        root1 = ET.fromstring(result1)
        root2 = ET.fromstring(result2)
        
        items1 = root1.findall('item')
        items2 = root2.findall('item')
        
        self.assertNotEqual(items1[0].find('billing_name').text, items2[0].find('billing_name').text)
    
    def test_anonymize_with_special_characters(self):
        """Test anonymization with special characters in names."""
        xml_special = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Cafe &amp; Restaurant Ltd.</billing_name>
    <billing_street>Rue de l'Ecole</billing_street>
    <billing_town>Montreal</billing_town>
    <billing_zip>H1A 1A1</billing_zip>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_special)
        root = ET.fromstring(result)
        item = root.find('item')
        
        self.assertIsNotNone(item.find('billing_name').text)
        self.assertNotEqual(item.find('billing_name').text, 'Cafe & Restaurant Ltd.')
    
    def test_anonymize_missing_fields(self):
        """Test that missing fields don't cause errors."""
        xml_missing = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <invoice_id>INV-001</invoice_id>
    <billing_name>Company A</billing_name>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_missing)
        root = ET.fromstring(result)
        item = root.find('item')
        
        self.assertNotEqual(item.find('billing_name').text, 'Company A')
        self.assertIsNone(item.find('billing_street'))


    def test_anonymize_delivery_fields(self):
        """Test that delivery fields are anonymized."""
        xml_with_delivery = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Company A</billing_name>
    <billing_street>Main Street</billing_street>
    <billing_town>Prague</billing_town>
    <billing_zip>11000</billing_zip>
    <delivery_name>John Doe</delivery_name>
    <delivery_street>Secondary Ave</delivery_street>
    <delivery_town>Brno</delivery_town>
    <delivery_zip>61200</delivery_zip>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_with_delivery)
        root = ET.fromstring(result)
        item = root.find('item')
        
        self.assertNotEqual(item.find('delivery_name').text, 'John Doe')
        self.assertNotEqual(item.find('delivery_street').text, 'Secondary Ave')
        self.assertNotEqual(item.find('delivery_town').text, 'Brno')
        self.assertNotEqual(item.find('delivery_zip').text, '61200')
    
    def test_anonymize_supplier_fields(self):
        """Test that supplier fields are anonymized."""
        xml_with_supplier = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Company A</billing_name>
    <supplier_company>Supplier Corp</supplier_company>
    <supplier_street>Supplier Street</supplier_street>
    <supplier_town>Supplier City</supplier_town>
    <supplier_zip>12345</supplier_zip>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_with_supplier)
        root = ET.fromstring(result)
        item = root.find('item')
        
        self.assertNotEqual(item.find('supplier_company').text, 'Supplier Corp')
        self.assertNotEqual(item.find('supplier_street').text, 'Supplier Street')
        self.assertNotEqual(item.find('supplier_town').text, 'Supplier City')
        self.assertNotEqual(item.find('supplier_zip').text, '12345')
    
    def test_anonymize_all_fields_together(self):
        """Test that billing, delivery, and supplier fields are all anonymized."""
        xml_complete = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <invoice_id>INV-001</invoice_id>
    <billing_name>Acme Corp</billing_name>
    <billing_street>Main St</billing_street>
    <billing_town>Prague</billing_town>
    <billing_zip>11000</billing_zip>
    <delivery_name>John Smith</delivery_name>
    <delivery_street>Oak Ave</delivery_street>
    <delivery_town>Brno</delivery_town>
    <delivery_zip>61200</delivery_zip>
    <supplier_company>Supplier Inc</supplier_company>
    <supplier_street>Industrial Rd</supplier_street>
    <supplier_town>Ostrava</supplier_town>
    <supplier_zip>70200</supplier_zip>
    <price_high>1000.00</price_high>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_complete)
        root = ET.fromstring(result)
        item = root.find('item')
        
        self.assertEqual(item.find('invoice_id').text, 'INV-001')
        self.assertEqual(item.find('price_high').text, '1000.00')
        
        self.assertNotEqual(item.find('billing_name').text, 'Acme Corp')
        self.assertNotEqual(item.find('billing_street').text, 'Main St')
        self.assertNotEqual(item.find('billing_town').text, 'Prague')
        self.assertNotEqual(item.find('billing_zip').text, '11000')
        
        self.assertNotEqual(item.find('delivery_name').text, 'John Smith')
        self.assertNotEqual(item.find('delivery_street').text, 'Oak Ave')
        self.assertNotEqual(item.find('delivery_town').text, 'Brno')
        self.assertNotEqual(item.find('delivery_zip').text, '61200')
        
        self.assertNotEqual(item.find('supplier_company').text, 'Supplier Inc')
        self.assertNotEqual(item.find('supplier_street').text, 'Industrial Rd')
        self.assertNotEqual(item.find('supplier_town').text, 'Ostrava')
        self.assertNotEqual(item.find('supplier_zip').text, '70200')
    
    def test_delivery_and_supplier_consistency(self):
        """Test that same delivery/supplier info is anonymized consistently."""
        xml_duplicate = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Company A</billing_name>
    <delivery_name>John Doe</delivery_name>
    <supplier_company>Supplier Corp</supplier_company>
  </item>
  <item>
    <billing_name>Company B</billing_name>
    <delivery_name>John Doe</delivery_name>
    <supplier_company>Supplier Corp</supplier_company>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_duplicate)
        root = ET.fromstring(result)
        items = root.findall('item')
        
        delivery_name_1 = items[0].find('delivery_name').text
        delivery_name_2 = items[1].find('delivery_name').text
        self.assertEqual(delivery_name_1, delivery_name_2)
        
        supplier_1 = items[0].find('supplier_company').text
        supplier_2 = items[1].find('supplier_company').text
        self.assertEqual(supplier_1, supplier_2)
    
    def test_anonymize_email_and_phone(self):
        """Test that email and phone are anonymized."""
        xml_with_contact = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Company A</billing_name>
    <email>john.doe@example.com</email>
    <phone>+420774832348</phone>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_with_contact)
        root = ET.fromstring(result)
        item = root.find('item')
        
        self.assertNotEqual(item.find('email').text, 'john.doe@example.com')
        self.assertNotEqual(item.find('phone').text, '+420774832348')
        self.assertIn('@', item.find('email').text)
        self.assertTrue(item.find('phone').text.startswith('+420'))
    
    def test_anonymize_supplier_ico_dic(self):
        """Test that supplier ICO and DIC are anonymized."""
        xml_with_ids = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Company A</billing_name>
    <supplier_company>Supplier Corp</supplier_company>
    <supplier_ico>70218463</supplier_ico>
    <supplier_dic>CZ7153150191</supplier_dic>
    <supplier_phone>+420776839021</supplier_phone>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_with_ids)
        root = ET.fromstring(result)
        item = root.find('item')
        
        self.assertNotEqual(item.find('supplier_ico').text, '70218463')
        self.assertNotEqual(item.find('supplier_dic').text, 'CZ7153150191')
        self.assertNotEqual(item.find('supplier_phone').text, '+420776839021')
        self.assertEqual(len(item.find('supplier_ico').text), 8)
        self.assertTrue(item.find('supplier_dic').text.startswith('CZ'))
    
    def test_email_phone_ico_dic_consistency(self):
        """Test that same email/phone/ico/dic values are anonymized consistently."""
        xml_duplicate = """<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <billing_name>Company A</billing_name>
    <email>test@example.com</email>
    <phone>+420123456789</phone>
    <supplier_ico>12345678</supplier_ico>
    <supplier_dic>CZ1234567890</supplier_dic>
  </item>
  <item>
    <billing_name>Company B</billing_name>
    <email>test@example.com</email>
    <phone>+420123456789</phone>
    <supplier_ico>12345678</supplier_ico>
    <supplier_dic>CZ1234567890</supplier_dic>
  </item>
</root>"""
        
        result = self.anonymizer.anonymize_string(xml_duplicate)
        root = ET.fromstring(result)
        items = root.findall('item')
        
        email_1 = items[0].find('email').text
        email_2 = items[1].find('email').text
        self.assertEqual(email_1, email_2)
        
        phone_1 = items[0].find('phone').text
        phone_2 = items[1].find('phone').text
        self.assertEqual(phone_1, phone_2)
        
        ico_1 = items[0].find('supplier_ico').text
        ico_2 = items[1].find('supplier_ico').text
        self.assertEqual(ico_1, ico_2)
        
        dic_1 = items[0].find('supplier_dic').text
        dic_2 = items[1].find('supplier_dic').text
        self.assertEqual(dic_1, dic_2)


class TestAnonymizerIntegration(unittest.TestCase):
    """Integration tests with actual fixture files."""
    
    def test_anonymize_sample_export(self):
        """Test anonymization with sample_export.xml fixture."""
        fixture_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'sample_export.xml')
        
        if not os.path.exists(fixture_path):
            self.skipTest(f"Fixture file not found: {fixture_path}")
        
        anonymizer = XMLAnonymizer(seed=42)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'anonymized.xml')
            result = anonymizer.anonymize_file(fixture_path, output_file)
            
            self.assertTrue(os.path.exists(result))
            
            tree = ET.parse(result)
            root = tree.getroot()
            items = root.findall('item')
            
            self.assertEqual(len(items), 2)
            
            for item in items:
                self.assertNotEqual(item.find('billing_name').text, 'Acme Corporation')
                self.assertNotEqual(item.find('billing_name').text, 'Beta Ltd')


if __name__ == '__main__':
    unittest.main()
