# TODO: make this and curl handler from vehicle fleet utility a single installable module

import os

import pycurl
from io import BytesIO
import json


class CurlHandler:
    def __init__(self):
        self.__curl = pycurl.Curl()
        self.__application_url = os.environ.get('VEHICLE_FLEET_URL') + ':8090'
        username = 'admin'
        password = 'password'
        self.__set_credentials(username, password)
        self.__curl.setopt(pycurl.VERBOSE, 1)

    def __del__(self):
        self.__curl.close()

    def __set_credentials(self, username, password):
        self.__curl.setopt(pycurl.USERPWD, '{}:{}'.format(username, password))

    def __send_curl_request(self, method, post_data=None):
        if post_data is None:
            self.__curl.setopt(pycurl.HTTPGET, True)
            self.__curl.unsetopt(pycurl.HTTPHEADER)
        else:
            self.__curl.setopt(pycurl.POST, 1)
            self.__curl.setopt(pycurl.POSTFIELDS, json.dumps(post_data))
            self.__curl.setopt(pycurl.HTTPHEADER, ['Content-type: application/json'])
        self.__curl.setopt(pycurl.URL, '{}/api/{}'.format(self.__application_url, method))
        buffer = BytesIO()
        self.__curl.setopt(pycurl.WRITEDATA, buffer)
        self.__curl.perform()
        status = self.__curl.getinfo(pycurl.RESPONSE_CODE)
        if status != 200:
            return None
        response_body = buffer.getvalue().decode('utf8')
        return json.loads(response_body)

    def get_vehicle_model_ids(self):
        result = self.__send_curl_request('vehicle_models')
        if result is None:
            return None
        return [model['id'] for model in result]

    def login(self, username, password):
        self.__set_credentials(username, password)
        # TODO: add login method to app API
        return self.get_vehicle_model_ids() is not None

    def get_distance_report(self, username, password, vehicle_id, time_unit, start, end):
        self.__set_credentials(username, password)
        result = self.__send_curl_request(
            'reports/distance/{}?timeunit={}&start={}&end={}'.format(
                vehicle_id, time_unit.upper(), start + "T00:00:00", end + "T00:00:00"))
        if result is None:
            return None
        results = result['result']
        return [(res['first'].split('T')[0], res['second']) for res in results]


