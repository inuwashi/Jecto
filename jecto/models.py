# Jecto Models

from django.db import models

class Zone(models.Model):
    name = models.CharField(max_length=32)
    weight = models.IntegerField()
    width = models.IntegerField()
    height = models.IntegerField()

    def __unicode__(self):
        return "[Z:%s/%s]" % (self.name, self.weight)

class Injection(models.Model):
    date = models.DateField()
    zone = models.ForeignKey(Zone)
    posX = models.IntegerField()
    posY = models.IntegerField()

    def __unicode__(self):
        return "[I:%s]" % self.date
