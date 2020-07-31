from django.db import models
from madrona.features.models import PolygonFeature, FeatureCollection, Feature, MultiPolygonFeature
from django.contrib.gis.db.models import MultiPolygonField
from django.db.models import Manager as GeoManager
from madrona.features import register, alternate, edit, get_feature_by_uid
from django.contrib.postgres.fields import JSONField
# from madrona.features.forms import SpatialFeatureForm

def sq_meters_to_sq_miles(area_m2):
    return area_m2/2589988.11

def sq_meters_to_acres(area_m2):
    return area_m2/4046.86

"""
    From MVC/MTV Components Doc

    Flatblock (django-flatblocks)
    #Flatpage (django-flatpages)
    MenuPage (Custom)
    Taxlot (custom)
    Property (madrona polygon-feature)
        We don't want to save these - creating them on the fly may be helpful, but we'll need to delete them immediately.
    ForestType
        will all data be aggregated to a single geometric model, or will there be a forest-type lookup to go with the feature layer?
    ReportPage (optional idea)
        Could capture "Get Help" content
        Could make any future updates/additions to the report more flexible
        Would totally %$&@ with some of the proposed views below (not good).
"""

class MenuPage(models.Model):
    name = models.CharField(max_length=255)
    order = models.SmallIntegerField(default=10)
    staff_only = models.BooleanField(default=False)
    content = models.TextField(null=True, blank=True, default=None)

    def __str__(self):
        return "%s" % self.name

# @register
# class Taxlot(MultiPolygonFeature):
#
#     class Options:
#         form = 'features.forms.SpatialFeatureForm'
#         manipulators = []
#
#     class Meta:
#         abstract = False

class Taxlot(models.Model):
    class Meta:
        verbose_name = 'Taxlot'
        verbose_name_plural = 'Taxlots'
        app_label = 'landmapper'

    shape_leng = models.FloatField(null=True, blank=True)
    shape_area = models.FloatField(null=True, blank=True)

    geometry = MultiPolygonField(
        srid=3857,
        null=True, blank=True,
        verbose_name="Grid Cell Geometry"
    )
    objects = GeoManager()

    @property
    def area_in_sq_miles(self):
        true_area = self.geometry.transform(2163, clone=True).area
        return sq_meters_to_sq_miles(true_area)

    @property
    def formatted_area(self):
        return int((self.area_in_sq_miles * 10) + .5) / 10.

    def serialize_attributes(self):
        attributes = []
        attributes.append({'title': 'Area', 'data': '%.1f sq miles' % (self.area_in_sq_miles)})
        # attributes.append({'title': 'Description', 'data': self.description})
        return { 'event': 'click', 'attributes': attributes }

    # @classmethod
    # def fill_color(self):
    #     return '776BAEFD'

    @classmethod
    def outline_color(self):
        return '776BAEFD'

    class Options:
        verbose_name = 'Taxlot'
        icon_url = None
        export_png = False
        manipulators = []
        optional_manipulators = []
        form = None
        form_template = None
        show_template = None

class Property(MultiPolygonFeature):
    # Property name
    def report_default():
        return {}

    # image field
    property_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    aerial_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    street_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    terrain_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    stream_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    soil_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)
    forest_map_image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=100, null=True)

    report_data = JSONField('report_data', default=report_default)

    @property
    def formatted_area(self):
        # return int((self.area_in_sq_miles * 10) +.5) / 10.
        area_acres = self.area_in_acres
        if area_acres < 10:
            return "%.2f" % area_acres
        if area_acres < 100:
            return "%.1f" % area_acres
        return "%.0f" % area_acres
        # return int((self.area_in_acres * 10) +.5) / 10.

    @property
    def area_in_sq_miles(self):
        return sq_meters_to_sq_miles(self.geometry_orig.area)

    @property
    def area_in_acres(self):
        return sq_meters_to_acres(self.geometry_orig.area)

    class Options:
        form = 'features.forms.SpatialFeatureForm'
        manipulators = []

    class Meta:
        abstract = False

class ForestType(models.Model):
    name = models.CharField(max_length=255)
