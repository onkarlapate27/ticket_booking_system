from django.db import models


class Passenger(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female')])
    is_child = models.BooleanField(default=False)
    has_child = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if self.age < 5:
            self.is_child = True
            self.has_child = False
        super().save(*args, **kwargs)

    def qualifies_for_lower_berth(self):
        """Returns True if the passenger qualifies for lower berth priority."""
        return self.age > 60 or (self.gender == 'F' and self.has_child)
    
    def __str__(self):
        return f"{self.name} ({self.age})"