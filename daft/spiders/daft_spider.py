import scrapy
import json

class DaftSpider(scrapy.Spider):
    name = "daft"
    api_key_header = "4f0649d1009e4de04bc96026f1e8f1b25b01e090"
    api_version_header = '1'
    app_headers = { 'X-Daft-API-Key': api_key_header, 'X-Daft-API-Version': api_version_header,
                    'No-Authentication': 'true' }

    def _generate_api_url(self, page_number, listing_type):
        """Return a valid daft.ie API url as a string."""
        base_url = 'https://api.daft.ie'
        url_path = '/vD8/json/search_{0}'.format(listing_type)
        parameters = '?parameters={{"query":{{"ad_type":"{0}","page":{1},"perpage":25,"sort_ascending":false,"sort_by":"priority_date"}},"api_key":"{2}"}}&source=android'.format(listing_type, page_number, self.api_key_header)
        return '{0}{1}{2}'.format(base_url, url_path, parameters)

    def generate_scraper_urls_for_sale(self):
        """Return a collection of all properties for sale in Ireland."""
        return scrapy.Request(url=self._generate_api_url(1, "sale"), callback=self.pagination, headers=self.app_headers)

    def _generate_media_api_url(self, ad_id):
        base_url = 'https://api.daft.ie'
        url_path = '/vD8/json/media'
        parameters = '?parameters={{"ad_id":{0},"ad_type":"{1}","api_key":"{2}"}}&source=android'.format(ad_id, "sale", self.api_key_header)
        return '{0}{1}{2}'.format(base_url, url_path, parameters)

    def pagination(self, response):
        api_results = json.loads(response.text)
        #from scrapy.shell import inspect_response
        #inspect_response(response, self)
        for property in api_results['result']['results']['ads']:
            ad_id = property['ad_id']
            yield scrapy.Request(url=self._generate_media_api_url(ad_id), callback=self.get_media_for_ad, headers=self.app_headers)
            yield property
        if api_results['result']['results']['pagination']['num_pages'] > api_results['result']['results']['pagination']['current_page']:
            yield scrapy.Request(url=self._generate_api_url(api_results['result']['results']['pagination']['current_page']+1, "sale"), callback=self.pagination, headers=self.app_headers)

    def get_media_for_ad(self, response):
        api_results = json.loads(response.text)
        all_media = []
        #from scrapy.shell import inspect_response
        #inspect_response(response, self)
        for media in api_results['result']['media']['images']:
            all_media.append([media['large_url'], media['caption']])
        yield json.loads('{{"ad_id": {0}, "media": {1}}}'.format(api_results['result']['media']['ad_id'], json.dumps(all_media)))


    def start_requests(self):
        yield self.generate_scraper_urls_for_sale()
