# Create your models here.
import hashlib
from django.db import models
from django.contrib.auth.models import User

class Paper(models.Model):
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='papers'
    )
    pdf_file = models.FileField(upload_to='uploaded_pdfs/')
    pdf_hash = models.CharField(max_length=64, blank=True, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    parse_type = models.CharField(
        max_length=50,
        choices=[
            ('references_only', 'References Only'),
            ('methods_tables_only', 'Methods & Tables Only'),
            ('both', 'Both References & Methods+Tables')
        ],
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Fields to store parse results
    references_json = models.TextField(blank=True)
    methods_text = models.TextField(blank=True)
    tables_json = models.TextField(blank=True)
    summary_text = models.TextField(blank=True)

    def __str__(self):
        return (self.title or self.pdf_file.name) + " (Owner: " + self.owner.username + ")"

    def save(self, *args, **kwargs):
        if self.pdf_file and not self.pdf_hash:
            self.pdf_hash = compute_file_hash(self.pdf_file)
        super().save(*args, **kwargs)

def compute_file_hash(file_field):
    hasher = hashlib.sha256()
    for chunk in file_field.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()


