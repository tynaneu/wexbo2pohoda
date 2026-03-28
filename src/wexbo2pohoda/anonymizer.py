import xml.etree.ElementTree as ET
import random
import string
from typing import Dict, Tuple


class XMLAnonymizer:
    """Anonymizes Wexbo XML files by replacing names and addresses."""
    
    FIELDS_TO_ANONYMIZE = {
        'billing_name': 'company',
        'billing_street': 'street',
        'billing_town': 'city',
        'billing_zip': 'zip',
    }
    
    def __init__(self, seed: int = None):
        """Initialize anonymizer with optional seed for reproducibility.
        
        Args:
            seed: Optional seed for random number generator for reproducible results
        """
        if seed is not None:
            random.seed(seed)
        self.name_mapping: Dict[str, str] = {}
        self.address_mapping: Dict[str, str] = {}
    
    def _generate_company_name(self) -> str:
        """Generate a random company name."""
        adjectives = ['Tech', 'Global', 'Smart', 'Prime', 'Elite', 'Nexus', 'Apex', 'Zenith']
        nouns = ['Solutions', 'Systems', 'Services', 'Corp', 'Ltd', 'Inc', 'Group', 'Labs']
        return f"{random.choice(adjectives)} {random.choice(nouns)}"
    
    def _generate_street_name(self) -> str:
        """Generate a random street name."""
        street_types = ['Street', 'Avenue', 'Road', 'Lane', 'Drive', 'Way', 'Court', 'Circle']
        street_names = ['Main', 'Oak', 'Elm', 'Pine', 'Maple', 'Cedar', 'Birch', 'Willow']
        return f"{random.choice(street_names)} {random.choice(street_types)}"
    
    def _generate_city_name(self) -> str:
        """Generate a random city name."""
        cities = ['Springfield', 'Riverside', 'Lakewood', 'Hillside', 'Greenfield', 
                  'Sunnyville', 'Brookside', 'Meadowbrook', 'Clearwater', 'Pinewood']
        return random.choice(cities)
    
    def _generate_zip_code(self) -> str:
        """Generate a random zip code."""
        return ''.join(random.choices(string.digits, k=5))
    
    def _generate_email(self) -> str:
        """Generate a random email address."""
        names = ['john', 'jane', 'alex', 'chris', 'pat', 'sam', 'taylor', 'morgan']
        domains = ['example.com', 'test.com', 'sample.org', 'demo.net', 'anon.io']
        return f"{random.choice(names)}{random.randint(100, 999)}@{random.choice(domains)}"
    
    def _generate_phone(self) -> str:
        """Generate a random phone number."""
        return f"+420{random.randint(100000000, 999999999)}"
    
    def _generate_ico(self) -> str:
        """Generate a random ICO (Czech company ID)."""
        return ''.join(random.choices(string.digits, k=8))
    
    def _generate_dic(self) -> str:
        """Generate a random DIC (Czech tax ID)."""
        return f"CZ{random.randint(10000000000, 99999999999)}"
    
    def _anonymize_name(self, original: str) -> str:
        """Anonymize a company name, maintaining consistency for duplicates.
        
        Args:
            original: Original company name
            
        Returns:
            Anonymized company name
        """
        if not original:
            return original
        
        if original not in self.name_mapping:
            self.name_mapping[original] = self._generate_company_name()
        
        return self.name_mapping[original]
    
    def _anonymize_address(self, field_type: str, original: str) -> str:
        """Anonymize an address field, maintaining consistency for duplicates.
        
        Args:
            field_type: Type of address field ('street', 'city', 'zip')
            original: Original address value
            
        Returns:
            Anonymized address value
        """
        if not original:
            return original
        
        key = f"{field_type}:{original}"
        
        if key not in self.address_mapping:
            if field_type == 'street':
                self.address_mapping[key] = self._generate_street_name()
            elif field_type == 'city':
                self.address_mapping[key] = self._generate_city_name()
            elif field_type == 'zip':
                self.address_mapping[key] = self._generate_zip_code()
        
        return self.address_mapping[key]
    
    def _anonymize_email(self, original: str) -> str:
        """Anonymize an email address, maintaining consistency for duplicates.
        
        Args:
            original: Original email address
            
        Returns:
            Anonymized email address
        """
        if not original:
            return original
        
        if original not in self.name_mapping:
            self.name_mapping[original] = self._generate_email()
        
        return self.name_mapping[original]
    
    def _anonymize_phone(self, original: str) -> str:
        """Anonymize a phone number, maintaining consistency for duplicates.
        
        Args:
            original: Original phone number
            
        Returns:
            Anonymized phone number
        """
        if not original:
            return original
        
        if original not in self.name_mapping:
            self.name_mapping[original] = self._generate_phone()
        
        return self.name_mapping[original]
    
    def _anonymize_ico(self, original: str) -> str:
        """Anonymize an ICO (company ID), maintaining consistency for duplicates.
        
        Args:
            original: Original ICO
            
        Returns:
            Anonymized ICO
        """
        if not original:
            return original
        
        if original not in self.name_mapping:
            self.name_mapping[original] = self._generate_ico()
        
        return self.name_mapping[original]
    
    def _anonymize_dic(self, original: str) -> str:
        """Anonymize a DIC (tax ID), maintaining consistency for duplicates.
        
        Args:
            original: Original DIC
            
        Returns:
            Anonymized DIC
        """
        if not original:
            return original
        
        if original not in self.name_mapping:
            self.name_mapping[original] = self._generate_dic()
        
        return self.name_mapping[original]
    
    def anonymize_file(self, input_file: str, output_file: str = None) -> str:
        """Anonymize an XML file and save to output.
        
        Args:
            input_file: Path to input XML file
            output_file: Path to output XML file (optional, auto-generated if not provided)
            
        Returns:
            Path to the anonymized output file
        """
        tree = ET.parse(input_file)
        root = tree.getroot()
        
        items = root.findall('item')
        for item in items:
            self._anonymize_item(item)
        
        if output_file is None:
            import os
            from datetime import datetime
            base_dir = os.path.dirname(input_file)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(base_dir, f"anonymized_{timestamp}.xml")
        
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        return output_file
    
    def anonymize_string(self, xml_string: str) -> str:
        """Anonymize XML from a string.
        
        Args:
            xml_string: XML content as string
            
        Returns:
            Anonymized XML as string
        """
        root = ET.fromstring(xml_string)
        items = root.findall('item')
        for item in items:
            self._anonymize_item(item)
        
        return ET.tostring(root, encoding='unicode')
    
    def _anonymize_item(self, item: ET.Element) -> None:
        """Anonymize a single item element in place.
        
        Args:
            item: XML element representing an item
        """
        self._anonymize_field(item, 'billing_name', 'name')
        self._anonymize_field(item, 'billing_street', 'street')
        self._anonymize_field(item, 'billing_town', 'city')
        self._anonymize_field(item, 'billing_zip', 'zip')
        self._anonymize_field(item, 'email', 'email')
        self._anonymize_field(item, 'phone', 'phone')
        
        self._anonymize_field(item, 'delivery_name', 'name')
        self._anonymize_field(item, 'delivery_street', 'street')
        self._anonymize_field(item, 'delivery_town', 'city')
        self._anonymize_field(item, 'delivery_zip', 'zip')
        
        self._anonymize_field(item, 'supplier_company', 'name')
        self._anonymize_field(item, 'supplier_street', 'street')
        self._anonymize_field(item, 'supplier_town', 'city')
        self._anonymize_field(item, 'supplier_zip', 'zip')
        self._anonymize_field(item, 'supplier_phone', 'phone')
        self._anonymize_field(item, 'supplier_ico', 'ico')
        self._anonymize_field(item, 'supplier_dic', 'dic')
    
    def _anonymize_field(self, item: ET.Element, field_name: str, field_type: str) -> None:
        """Anonymize a single field in an item.
        
        Args:
            item: XML element representing an item
            field_name: Name of the field to anonymize
            field_type: Type of field ('name', 'street', 'city', 'zip', 'email', 'phone', 'ico', 'dic')
        """
        elem = item.find(field_name)
        if elem is not None and elem.text:
            if field_type == 'name':
                elem.text = self._anonymize_name(elem.text)
            elif field_type == 'email':
                elem.text = self._anonymize_email(elem.text)
            elif field_type == 'phone':
                elem.text = self._anonymize_phone(elem.text)
            elif field_type == 'ico':
                elem.text = self._anonymize_ico(elem.text)
            elif field_type == 'dic':
                elem.text = self._anonymize_dic(elem.text)
            else:
                elem.text = self._anonymize_address(field_type, elem.text)
