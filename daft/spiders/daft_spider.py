import scrapy
import json
import lxml

class DaftSpider(scrapy.Spider):
    name = "daft"

    def _generate_url(self, action, property_type, sw, ne):
        """Return a valid daft.ie URL as a string."""
        sw[0] += (".03173528395185")
        sw[1] += (".03197265625")
        ne[0] += (".031189853816535")
        ne[1] += (".59498046875")
        base_url = 'http://www.daft.ie/ajax_endpoint.php?action='
        extra_params = ('&extra_params={{"rent"%3A[0%2C50000000]'
                        '%2C"beds"%3A[0%2C20]}}')
        url = '{0}{1}&type={2}&sw=({3}%2C+{4})&ne=({5}%2C+{6}){7}'.format(
            base_url, action, property_type, sw[0], sw[1], ne[0], ne[1],
            extra_params)

        return url

    def _divvy_up_ireland(self):
        """Return a list of coordinates covering Ireland."""
        with open('coordinates.json') as data_file:
            data = json.load(data_file)
        return data

    def generate_scraper_urls_for_sale(self):
        """Return a collection of all properties for sale in Ireland."""
        urls = []
        for coords in self._divvy_up_ireland():
            url = self._generate_url('map_nearby_properties', 'sale', coords['sw'], coords['ne'])
            urls.append(url)
        return urls

    def start_requests(self):
        urls = self.generate_scraper_urls_for_sale()
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, meta={'handle_http_status_list': [301]})


    def parse(self, response):
        result_data = json.loads(response.text)
        for property in result_data:
            url = "http://www.daft.ie" + property['link']
            yield scrapy.Request(url=url, callback=self.parse_property_images, meta={'handle_http_status_list': [301]})
            yield property

    def parse_property_images(self, response):
        """stolen from https://github.com/Danm72/DaftPy"""
        # TODO I can drop the lxml requirement now, and use scrapy
        tree = lxml.html.fromstring(response.text)
        results = tree.cssselect('#pbxl_carousel ul li.pbxl_carousel_item img')
        images = []
        for image in results:
            url = image.get('src')
            if url.startswith('//'):
                url = 'https:' + url
            images.append(url)
        yield { 'id': response.css('li#saved-ad::attr(data-adid)').extract()[0],
                'results': images,
              }

