from django.shortcuts import render
from .models import QRCode
import qrcode
import cv2
import uuid
import os
from django.core.files.storage import FileSystemStorage
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from pathlib import Path


# Create your views here.

def home(request):
    return render(request, 'scanner/home.html')


def generate_qr(request):
    qr_image_url = None

    if request.method == 'POST':
        data = request.POST.get("qr_data")
        mobile_number = request.POST.get("mobile_number")

        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            return render(
                request,
                'scanner/generate_qr.html',
                {'error': "Invalid mobile number. Please enter a 10-digit number."}
            )

        qr_content = f"{data}|{mobile_number}"

        qr = qrcode.make(qr_content)

        qr_image_io = BytesIO()
        qr.save(qr_image_io, format='PNG')
        qr_image_io.seek(0)

        qr_storage_path = os.path.join(settings.MEDIA_ROOT, 'qr_codes')

        os.makedirs(qr_storage_path, exist_ok=True)

        fs = FileSystemStorage(
            location=qr_storage_path,
            base_url='/media/qr_codes/'
        )

        # Safe filename
        filename = f"{uuid.uuid4()}.png"

        qr_image_content = ContentFile(
            qr_image_io.read(),
            name=filename
        )

        fs.save(filename, qr_image_content)

        qr_image_url = fs.url(filename)

        QRCode.objects.create(
            data=data,
            mobile_number=mobile_number,
            qr_image=filename
        )

    return render(
        request,
        'scanner/generate_qr.html',
        {"qr_image_url": qr_image_url}
    )


def scan_qr(request):
    result = None

    if request.method == 'POST' and request.FILES.get("qr_image"):

        mobile_number = request.POST.get("mobile_number")
        qr_image = request.FILES['qr_image']

        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            return render(
                request,
                'scanner/scan_qr.html',
                {'error': "Invalid mobile number. Please enter a 10-digit number."}
            )

        fs = FileSystemStorage()
        filename = fs.save(qr_image.name, qr_image)

        image_path = Path(fs.location) / filename

        try:
            # Read image using OpenCV
            image = cv2.imread(str(image_path))

            if image is None:
                result = "Unable to read image file."
            else:
                detector = cv2.QRCodeDetector()

                qr_content, points, _ = detector.detectAndDecode(image)

                if qr_content:

                    try:
                        qr_data, qr_mobile_number = qr_content.strip().split('|')

                        qr_entry = QRCode.objects.filter(
                            data=qr_data,
                            mobile_number=qr_mobile_number
                        ).first()

                        if qr_entry and qr_mobile_number == mobile_number:

                            result = "Scan Success: Valid QR Code for the provided mobile number."

                            qr_image_path = os.path.join(settings.MEDIA_ROOT, 'qr_codes', qr_entry.qr_image)

                            # Delete generated QR image
                            if qr_image_path.exists():
                               qr_image_path.unlink()
                               
                            # Delete uploaded image
                            if image_path.exists():
                                image_path.unlink()

                            # Delete database record
                            qr_entry.delete()
                            # qr_image_path.delete()

                        else:
                            result = "Scan Failed: Invalid QR Code or mobile number mismatch."

                    except ValueError:
                        result = "Invalid QR Code format."

                else:
                    result = "No QR Code detected in the image."

        except Exception as e:
            result = f"Error processing image: {str(e)}"

        finally:
            if image_path.exists():
                image_path.unlink()

    return render(
        request,
        'scanner/scan_qr.html',
        {"result": result}
    )
