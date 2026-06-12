from django.db import models

# Create your models here.
class QRCode(models.Model):
  data = models.CharField(max_length=223)
  mobile_number=models.CharField(max_length=12)
  qr_image = models.CharField(max_length=255)

  def __str__(self):
    return f"{self.data}-{self.mobile_number}-{self.qr_image}"