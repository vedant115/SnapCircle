import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
import io
import base64
import os
from typing import Optional

def generate_event_qr_code(
    event_code: str,
    base_url: str = None,
    size: int = 10,
    border: int = 4
) -> str:
    """
    Generate a QR code for event registration.

    Args:
        event_code: The event code (6-character string)
        base_url: Base URL of the frontend application (if None, uses environment variable)
        size: Size of the QR code (1-40)
        border: Border size around the QR code

    Returns:
        Base64 encoded PNG image of the QR code
    """
    # Get frontend URL from environment or use provided base_url
    if base_url is None:
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Create the registration URL
    registration_url = f"{base_url}/join/{event_code}"
    
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,  # Controls the size of the QR Code
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    
    # Add data to the QR code
    qr.add_data(registration_url)
    qr.make(fit=True)
    
    # Create image with styled appearance
    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        fill_color="black",
        back_color="white"
    )
    
    # Convert to base64 string
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Encode to base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"

def generate_simple_qr_code(
    data: str,
    size: int = 10,
    border: int = 4
) -> str:
    """
    Generate a simple QR code for any data.
    
    Args:
        data: The data to encode in the QR code
        size: Size of the QR code (1-40)
        border: Border size around the QR code
    
    Returns:
        Base64 encoded PNG image of the QR code
    """
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    
    # Add data to the QR code
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 string
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    # Encode to base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"
