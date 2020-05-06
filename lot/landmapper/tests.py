from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver

from django.test import TestCase
from django.conf import settings
from django.urls import reverse

class ModelTests(TestCase):
    """
    Queries on each model in the module
        Queries return correct data
        Queries that should return no data get no data
    """

    # How to work with GEOS API in Django:
    #       https://docs.djangoproject.com/en/2.2/ref/contrib/gis/geos/

    def setUp(self):
        from django.contrib.auth.models import User
        # from landmapper.models import Taxlot
        # from django.contrib.gis.geos import GEOSGeometry
        ### Create user
        User.objects.get_or_create(username='admin')

    def test_taxlot(self):
        from django.contrib.auth.models import User
        from landmapper.models import Taxlot
        from django.contrib.gis.geos import GEOSGeometry

        admin = User.objects.get(username='admin')

        ### Create Taxlots
        # ZOOM TO: 44.085, -122.900
        # Taxlot NE of Eugene:
        poly_1 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13681279.3108 5478566.238799997, -13680721.1384 5478574.5858, -13680722.0809 5478015.218999997, -13681279.9385 5478006.679099999, -13681838.8572 5477998.089199997, -13681837.4829 5478557.857699998, -13681279.3108 5478566.238799997)))', srid=3857)
        # Adjacent taxlot to the note
        poly_2 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13681278.5741 5479125.020800002, -13680719.8309 5479133.516500004, -13680721.1384 5478574.5858, -13681279.3108 5478566.238799997, -13681837.4829 5478557.857699998, -13681837.3172 5479116.491499998, -13681278.5741 5479125.020800002)))', srid=3857)
        # Nearby, non-adjacent taxlot
        poly_3 = GEOSGeometry('SRID=3857;MULTIPOLYGON (((-13679606.0781 5478590.317100003, -13679607.5092 5478031.919799998, -13680164.0094 5478023.597900003, -13680163.6087 5478582.451800004, -13679606.0781 5478590.317100003)))', srid=3857)
        # transform polies from 3857 to 4326
        poly_1.transform(4326)
        poly_2.transform(4326)
        poly_3.transform(4326)

        #Create taxlot instances
        tl1 = Taxlot.objects.create(user=admin, geometry_orig=poly_1)
        tl2 = Taxlot.objects.create(user=admin, geometry_orig=poly_2)
        tl3 = Taxlot.objects.create(user=admin, geometry_orig=poly_3)

        click_1 = 'SRID=4326;POINT( -122.903 44.083 )'          #Note, it doesn't appear to matter if we give GEOSGeoms or just WKT.
        click_2 = GEOSGeometry('SRID=4326;POINT( -122.902 44.087 )')
        click_3 = GEOSGeometry('SRID=4326;POINT( -122.888 44.083 )')
        click_4 = GEOSGeometry('SRID=4326;POINT( -123 45 )')

        # Test intersection
        taxlot_1 = Taxlot.objects.get(geometry_orig__contains=click_1)
        taxlot_2 = Taxlot.objects.get(geometry_orig__contains=click_2)
        taxlot_3 = Taxlot.objects.get(geometry_orig__contains=click_3)
        self.assertEqual(taxlot_1.pk, tl1.pk)
        self.assertEqual(taxlot_2.pk, tl2.pk)
        self.assertEqual(taxlot_3.pk, tl3.pk)
        self.assertNotEqual(taxlot_1.pk, tl2.pk)
        self.assertEqual(len(Taxlot.objects.filter(geometry_orig__contains=click_4)), 0)

        #TODO: test any model methods for attributes and types returned

    def test_menu_page(self):
        from landmapper.models import MenuPage

        menu_title = "Menu Item"
        # Courtesy of rikeripsum.com
        menu_text = "The game's not big enough unless it scares you a little. \
        Your head is not an artifact! Our neural pathways have become \
        accustomed to your sensory input patterns. Commander William Riker of \
        the Starship Enterprise. What? We're not at all alike! What's a \
        knock-out like you doing in a computer-generated gin joint like this? \
        Not if I weaken first. Mr. Worf, you sound like a man who's asking his \
        friend if he can start dating his sister. For an android with no \
        feelings, he sure managed to evoke them in others."
        menu_content = "<h1>%s</h1><p>%s</p>" % (menu_title, menu_text)

        MenuPage.objects.create(name='Menu', content=menu_content, order=0)

        hipster_title = "Hipster"
        # courtesy of https://hipsum.co/
        hipster_textP1 = "Fam id messenger bag forage, nisi lomo edison bulb \
        ipsum lo-fi kitsch street art kinfolk sriracha irony nulla. Raclette \
        fanny pack meditation, lomo heirloom farm-to-table wayfarers shaman \
        dolore roof party trust fund disrupt laboris anim kogi. Taxidermy \
        organic nostrud blue bottle activated charcoal minim, gluten-free \
        slow-carb XOXO photo booth cornhole keffiyeh elit. Cold-pressed \
        cornhole waistcoat snackwave hexagon. Banh mi subway tile viral ennui, \
        duis irure poutine proident flexitarian fam direct trade sint roof \
        party. Try-hard artisan pork belly chillwave. Quis activated charcoal \
        mustache cornhole excepteur nostrud godard."
        hipster_textP2 = "Id neutra literally four dollar toast ea, franzen \
        irony food truck venmo. Pour-over copper mug cold-pressed, yr YOLO \
        sartorial tousled pug tacos mustache hashtag. Health goth vinyl \
        chillwave williamsburg cardigan kickstarter tofu normcore duis hoodie \
        shaman neutra cred tumblr church-key. Af authentic craft beer, \
        letterpress deep v intelligentsia slow-carb synth 90's. Activated \
        charcoal organic blue bottle aliqua in dolore."
        hipster_content = "<h1>%s</h1><p>%s</p><p>%s</p>" % (
            hipster_title,
            hipster_textP1,
            hipster_textP2
        )

        MenuPage.objects.create(name=hipster_title, content=hipster_content, order=1, staff_only=True)

        self.assertEqual(len(MenuPage.objects.all()), 2)
        non_staff = MenuPage.objects.get(staff_only=False)
        self.assertTrue('gin joint' in non_staff.content)
        staff_only = MenuPage.objects.get(staff_only=True)
        self.assertTrue('Banh mi' in staff_only.content)

        # TODO: test this in Front-End

    def test_forest_type(self):
        from landmapper.models import ForestType

        ForestType.objects.create(name='Foo')

        self.assertEqual(len(ForestType.objects.all()), 1)

        # TODO: test everything about ForestType once it's a thing

class ViewTests(TestCase):
    """
    External APIs
        soil data queries
        geocoding
        Pulling map images for server-side .PDF creation
    """
    def test_soils_api(self):
        from osgeo import ogr
        from landmapper.views import get_soils_connectors, get_soil_data_gml, get_soils_list
        (wms, wfs) = get_soils_connectors()
        # Good examples: https://geopython.github.io/OWSLib/#wms
        self.assertEqual(wms.identification.type, 'OGC:WMS')
        self.assertTrue(wms.identification.version in ['1.1.0', '1.1.1', '1.3.0'])
        self.assertEqual(wms.identification.title, 'NRCS Soil Data Mart Data Access Web Map Service')
        self.assertEqual(wms.identification.abstract, 'NRCS SSURGO Soils web map service. This is an Open GIS Consortium standard Web Map Service (WMS).')
        self.assertTrue('Soils' in list(wms.contents))
        self.assertEqual(wms['Soils'].title, 'Soils')
        # self.assertTrue('ESPG:3857' in wms['Soils'].crsOptions)
        self.assertEqual(
            wms['Soils'].styles['default']['legend'],
            'https://SDMDataAccess.sc.egov.usda.gov/Spatial/SDM.wms?version=1.1.1&service=WMS&request=GetLegendGraphic&layer=Soils&format=image/png&STYLE=default'
        )
        img = wms.getmap(
            # layers=['surveyareapoly'],
            layers=[settings.SOIL_TILE_LAYER],
            styles=['default'],
            # srs='EPSG:4326',
            # bbox=(-125, 36, -119, 41),
            srs='EPSG:3857',
            bbox=(-13505988.11665581167,5460691.044468306005,-13496204.17703530937,5473814.764981821179),
            size=(665,892), # WIDTH=665&HEIGHT=892
            format='image/png',
            tansparent=True
        )
        out = open('%s.png' % settings.SOIL_TILE_LAYER, 'wb')
        out.write(img.read())
        out.close()

        # gml = get_soil_data_gml('-121.32635552328541,43.969290485490596,-121.325,43.97', 'EPSG:4326', 'GML3') #TinyExample
        # soils_list = get_soils_list('-121.32635552328541,43.969290485490596,-121.23846489828543,44.054078446801526', 'EPSG:4326') # Bend
        # soils_list_mercator = get_soils_list('-13505988.11665581167,5460691.044468306005,-13496204.17703530937,5473814.764981821179', 'EPSG:3857') # Bend
        soils_list = get_soils_list('-13505988.11665581167,5460691.044468306005,-13496204.17703530937,5473814.764981821179', 'EPSG:3857') # Bend
        #
        # soils_list.keys() == soils_list_mercator.keys()

        self.assertEqual(len(soils_list.keys()), 18)
        self.assertEqual(soils_list['W']['muname'], 'Water')
        for musym in ['61C', '157C', '62D', '155C', '155D', '58C', '72C', '36A', '28A', '27A', '65A', '156C', '38B', '85A', '18D', '36B', 'W', 'NOTCOM']:
            self.assertTrue(musym in soils_list.keys())

        print('soils')

    def test_geocoding(self):
        from landmapper.views import geocode

        coords = geocode('Mountain View, CA')

        self.assertEqual(coords, [37.389670000000024, -122.08159999999998])
        print('geocoder')

    def test_tiles(self):
        # TODO: Tile requests
        #   basemap images
        #   streams?
        #   lots/properties?
        #   forest types?
        #   soils
        """
        get BBOX, centroid, zoom, or any other value needed to query the endpoints
        get basemap tile
        -   set
        get any overlay tiles
        stitch images together (imagemagic?)
        """

        # BBOX

        # Convert to height, width, zoom, centroid, etc... ?

        # Basemap endpoints
        #   Aerial (ArcGIS) is an XYZ - can we query for BBOX instead?
        #       https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/7/44/32
        #       Examples here: https://developers.arcgis.com/rest/services-reference/export-image.htm
        #       https://sampleserver3.arcgisonline.com/ArcGIS/rest/services/World/MODIS/ImageServer/exportImage?f=image&bbox=-141.19530416221985,-62.217823180545146,139.27427961579508,84.15317625109763&imageSR=4326&bboxSR=4326&size=937,489
        #       https://sampleserver3.arcgisonline.com/ArcGIS/rest/services/World/MODIS/ImageServer/exportImage?f=image&
        #           bbox=-141.19530416221985,-62.217823180545146,139.27427961579508,84.15317625109763&
        #           imageSR=4326&
        #           bboxSR=4326&
        #           size=937,489

        # From Bend Soils Example:
        # srs='EPSG:3857',
        # bbox=(-13505988.11665581167,5460691.044468306005,-13496204.17703530937,5473814.764981821179),
        # size=(665,892), # WIDTH=665&HEIGHT=892

        from landmapper.views import get_aerial_image
        bbox = '-13505988.11665581167,5460691.044468306005,-13496204.17703530937,5473814.764981821179'
        bboxSR = 3857
        width = 665
        height = 892
        image_dict = get_aerial_image(bbox, width, height, bboxSR)
        # aerial_endpoint = 'https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/export'
        # layers = 0
        # aerial_url = "%s?bbox=%s&imageSR=3857&bboxSR=%s&layers=%s&size=%s,%s&format=png&f=image" % (aerial_endpoint, bbox, bboxSR, layers, width, height)
        # attribution = 'USGS The National Map: Orthoimagery. Data refreshed April, 2019.'
        out = open('aerial.png', 'wb')
        out.write(image_dict['image'].read())
        out.close()


        print('tiles')

    """
    Templates
        correctly formatted context for rendering templates
        reporting values
        ForestType queries
        legend creation (map, forest type, soil)
        table creation (overview, forest type, soil)
    """

    # Should we break up views into 'gather' and 'render' functions?
    # Perhaps the 'gather' functions are modular children - the parent requests
    #   the context and then uses that to render the template

    def test_header_gather(self):
        # TODO:
        # add menu items (done in models tests?)
        # do branding images exist?
        # is context dict correctly formatted with:
        #   correct keywords
        #   correct value types for each keyword
        #   correct values
        #   correct order (of MenuPage instances)
        print('header view')

    def test_home_view_gather(self):
        # TODO:
        #   ...
        print('home view gather')

    def test_index_page(self):
        """
            TODO:
                create variable to strore result of fetching the home page
                assert response is 200
        """
        from landmapper.views import index
        response = self.client.get(reverse(index))
        self.assertEqual(response.status_code, 200)

    def test_identify_gather(self):
        """
        Test:
            Input
        TODO:
            create var to store page request input
            check for a coords param
            check for a search string
            check for taxlot ids param
            check for property name param
        IN:
            coords
            search string
            (opt) taxlot ids
            (opt) property name
        """
        # from landmapper.views import identify
        print('test identify gather')

    def test_identify_render(self):
        """
        TEST:
            Rendered Template
        TODO:
            create variable to store result of fetching the identify page
            assert response is 200
        """
        from landmapper.views import identify
        response = self.client.get(reverse(identify))
        self.assertEqual(response.status_code, 200)

    def test_report_gather(self):
        """
        Test:
            IN
        TODO:
            create var to store page request input
            check for taxlot ids
            check for property name
        IN:
            taxlot ids
            property name
        """
        # from landmapper.views import report
        print('test report gather')

    def test_report_render(self):
        """
        TEST:
            Rendered Template
        TODO:
            create variable to store result of fetching the report page
            assert response is 200
            can a property be created
            can a report be created
            is a legend returned

        USES:
            CreateProperty, CreatePDF, ExportLayer, BuildLegend, BuildTables
        """
        from landmapper.views import report
        response = self.client.get(reverse(report))
        self.assertEqual(response.status_code, 200)

    def test_create_property(self):
        """
        TODO:
            make request to create a property with paramaters for:
                taxlot_ids[]
                property_name
            check if a madrona polygon feature is returned
        NOTES:
            should be cached
        """
        # from landmapper.views import create_property
        print('property created')

    """
    Error Handling
    """
    """
    GIS Manipulation
        convert taxlot selections into features
    """
    """
    File generation/export
        pdf report generation
            all
            forest type
            soil
        Property Shapefile
            zipping
    """
    def test_views(self):
        print("Views!")

class FrontendTests(StaticLiveServerTestCase):
    """
    state changes
        address found
            map zoomed
                Test if specific map tiles were pulled
            state advanced
        1st taxlot selected
            state advanced
            url updated
        2nd taxlot selected
            state retained
            url updated
        property name entered
            'next' enabled
            url updated
        property name deleted
            'next' disabled
            url updated
        2nd taxlot unselected
            url updated
            state retained
        1st taxlot unselected
            url updated
            state regressed
        address cleared
            url updated
            state regressed
            map zoomed back to default
        valid input and clicking 'next' brings us to a report
    Error handling
        unknown address
        non-contiguous taxlots
    validation
        validate address prior to geocode query
        valid property names?
            1+ spaces?
            Maximum characters
            Foreign accented characters (Latin1, umlauts, etc…)
    popups
        From the header menu
        from the download button(s)
        From 'get help'
    downloads?
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.selenium = WebDriver()
        cls.selenium.implicitly_wait(2)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    # def test_home(self):
    #    # TODOS:
    #    #   Header placement
    #    #   Header branding
    #    #   Header Menu Items
    #    #   ...
    #    print("hi")

    # def test_login(self):
    def test_browser(self):
        print("Front End!")

# class MySeleniumTests(StaticLiveServerTestCase):
#     # fixtures = ['user-data.json']
#     #
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.selenium = WebDriver()
#         cls.selenium.implicitly_wait(2)
#
#     @classmethod
#     def tearDownClass(cls):
#         cls.selenium.quit()
#         super().tearDownClass()
#
#     # def test_login(self):
#     def test_browser(self):
#         # import ipdb; ipdb.set_trace()
#         print('get server')
#         print('URL: ""%s"' % self.live_server_url)
#         # foo = self.selenium.get(self.live_server_url)
#         # foo.title
#         # self.selenium.get('%s%s' % (self.live_server_url, '/login/'))
#         # username_input = self.selenium.find_element_by_name("username")
#         # username_input.send_keys('myuser')
#         # password_input = self.selenium.find_element_by_name("password")
#         # password_input.send_keys('secret')
#         # self.selenium.find_element_by_xpath('//input[@value="Log in"]').click()
#




# from django.test import TestCase
#
# from selenium import webdriver
#
# # From stack overflow:
# ### https://stackoverflow.com/a/47785513
# from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#
# cap = DesiredCapabilities().FIREFOX
# # cap["marionette"] = False
#
# # browser = webdriver.Firefox(capabilities=cap, executable_path="/usr/local/bin/geckodriver")
#
# ### https://stackoverflow.com/questions/45692626/unable-to-load-firefox-in-selenium-webdriver-in-python
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
# cap["marionette"] = True
# binary = FirefoxBinary('/usr/bin/firefox')
# print('create browser')
# browser = webdriver.Firefox(firefox_binary=binary, capabilities=cap, executable_path="/usr/local/bin/geckodriver")
#
# # browser = webdriver.Firefox()
# # browser.get('http://127.0.0.1:8000')
# print('google test')
# browser.get('http://www.google.com')
# print('pre')
# browser.get('http://0:8000')
# print(browser.title)
# assert 'Django' in browser.title
