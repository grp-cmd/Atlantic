"""Utility functions for calculations"""
from math import radians, sin, cos, sqrt, atan2
from config import PORTS_DATABASE

class PortCalculator:
    @staticmethod
    def calculate_distance(lat1, lon1, lat2, lon2):
        """Haversine formula - nautical miles"""
        R = 3440.065
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))
    
    @staticmethod
    def estimate_transit_time(distance_nm, speed=20):
        """Transit time in days"""
        return round(distance_nm / speed / 24, 1)
    
    @staticmethod
    def find_port(country, city):
        """Find port info"""
        country, city = country.lower(), city.lower().replace(" ", "")
        return PORTS_DATABASE.get(country, {}).get(city)

class FreightCalculator:
    @staticmethod
    def calculate_cost(distance_nm, weight_tons, cargo_type="general", container="20ft"):
        """Calculate shipping costs"""
        from config import CARGO_TYPES
        
        base_rate = 0.15
        cargo_factor = CARGO_TYPES.get(cargo_type, {}).get("factor", 1.0)
        container_mult = 1.8 if "40ft" in container else 1.0
        
        freight = distance_nm * weight_tons * base_rate * cargo_factor * container_mult
        bunker = freight * 0.15
        terminal = 300 * (2 if "40ft" in container else 1)
        
        return {
            "base_freight": round(freight),
            "bunker_surcharge": round(bunker),
            "terminal_handling": terminal,
            "documentation": 150,
            "customs_broker": 500,
            "insurance": round(freight * 0.02),
            "total": round(freight + bunker + terminal + 150 + 500 + freight * 0.02)
        }

class PDFGenerator:
    """PDF generation (optional)"""
    @staticmethod
    def generate_quote_pdf(data):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from io import BytesIO
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            elements.append(Paragraph("ATLANTIS SHIPPING QUOTE", styles['Title']))
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Route: {data['origin']} to {data['dest']}", styles['Normal']))
            elements.append(Paragraph(f"Total Cost: ${data['total']:,.2f}", styles['Heading2']))
            
            doc.build(elements)
            buffer.seek(0)
            return buffer
        except:
            return None
