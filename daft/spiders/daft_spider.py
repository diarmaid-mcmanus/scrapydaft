import scrapy
import json

class DaftSpider(scrapy.Spider):
    name = "daft"
    api_key_header = "4f0649d1009e4de04bc96026f1e8f1b25b01e090"
    api_version_header = '1'
    app_headers = { 'X-Daft-API-Key': api_key_header, 'X-Daft-API-Version': api_version_header,
                    'No-Authentication': 'true' }
    api_url = 'https://api.daft.ie'
    api_path = '/vD8/json/'

    def _generate_api_url(self, endpoint, parameters):
        return '{0}{1}{2}?parameters={3}&source=android'.format(self.api_url, self.api_path, endpoint, parameters)

    def _generate_search_url(self, page_number, listing_type):
        """Return a valid daft.ie API url as a string."""
        endpoint = 'search_{0}'.format(listing_type)
        parameters = '{{"query":{{"ad_type":"{0}","page":{1},"perpage":25,"sort_ascending":false,"sort_by":"priority_date"}},"api_key":"{2}"}}'.format(listing_type, page_number, self.api_key_header)
        return self._generate_api_url(endpoint, parameters)

    def _generate_media_url(self, ad_id):
        parameters = '{{"ad_id":{0},"ad_type":"{1}","api_key":"{2}"}}'.format(ad_id, "sale", self.api_key_header)
        return self._generate_api_url('media', parameters)

    def parse_search(self, response):
        api_results = json.loads(response.text)
        current_page = api_results['result']['results']['pagination']['current_page']
        num_pages = api_results['result']['results']['pagination']['num_pages']
        current_property = 0
        for property in api_results['result']['results']['ads']:
            ad_id = property['ad_id']
            current_property = current_property+1
            self.logger.debug("DAFTDEBUG yielding Media request {0} {1}".format(ad_id, self.calculate_additional_debug(current_property)))
            yield scrapy.Request(url=self._generate_media_url(ad_id), callback=self.parse_media, headers=self.app_headers)
            self.logger.debug("DAFTDEBUG yielding property {0} {1}".format(ad_id, self.calculate_additional_debug(current_property)))
            yield property
        if num_pages > current_page:
            self.logger.debug("DAFTDEBUG yielding page {0} of {1}".format(current_page+1, num_pages))
            yield scrapy.Request(url=self._generate_search_url(current_page+1, "sale"), callback=self.parse_search, headers=self.app_headers)

    def calculate_additional_debug(self, num):
        if num % 5 == 0:
            return "{0}".format(num)
        else:
            return ""

    def parse_media(self, response):
        api_results = json.loads(response.text)
        all_media = []
        for media in api_results['result']['media']['images']:
            all_media.append([media['large_url'], media['caption']])
        yield json.loads('{{"ad_id": {0}, "media": {1}}}'.format(api_results['result']['media']['ad_id'], json.dumps(all_media)))


    def start_requests(self):
        self.logger.debug("I am doing the thing")
        yield scrapy.Request(url=self._generate_search_url(1, "sale"), callback=self.parse_search, headers=self.app_headers)
