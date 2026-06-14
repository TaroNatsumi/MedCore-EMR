from django.db import models

class TempDecryptedSession(models.Model):
    session_id = models.CharField(max_length=255, unique=True)
    doctor_id = models.IntegerField()
    patient_pinfl = models.CharField(max_length=14)
    record_id = models.IntegerField(null=True, blank=True) # ID of the EncryptedMedicalRecord (if editing)
    
    decrypted_data = models.JSONField(verbose_name="Временные дешифрованные данные")
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session {self.session_id} for Doctor ID {self.doctor_id}"
