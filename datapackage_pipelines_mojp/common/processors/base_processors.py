from itertools import chain
from datapackage_pipelines.wrapper import ingest, spew
from datapackage_pipelines_mojp import settings as mojp_settings
import logging
import json


class BaseProcessor(object):
    """
    all mojp processor should extend this class
    it is pluggable into our unit tests to allow mocks and automated tests of processors
    """

    def __init__(self, parameters, datapackage, resources, settings=None):
        self._parameters = parameters
        self._datapackage = datapackage
        self._resources = resources
        self._settings = mojp_settings if not settings else settings

    @classmethod
    def main(cls):
        # can be used like this in datapackage processor files:
        # if __main__ == '__main__':
        #      Processor.main()
        spew(*cls(*ingest()).spew())

    def spew(self):
        self._datapackage, self._resources = self._process(self._datapackage, self._resources)
        return self._datapackage, self._resources

    def _process(self, datapackage, resources):
        return datapackage, resources

    def _get_settings(self, key=None, default=None):
        if key:
            ret = getattr(self._settings, key, default)
            if default is None and ret is None:
                raise Exception("unknown key: {}".format(key))
            else:
                return ret
        else:
            return self._settings


class AddResourcesProcessor(BaseProcessor):

    def _get_resource_descriptors(self):
        return []

    def _get_resources_iterator(self):
        return ()

    def _process(self, datapackage, resources):
        datapackage["resources"] += self._get_resource_descriptors()
        resources = chain(resources, self._get_resources_iterator())
        return super(AddResourcesProcessor, self)._process(datapackage, resources)


class FilterResourcesProcessor(BaseProcessor):

    def _filter_datapackage(self, datapackage):
        datapackage["resources"] = self._filter_resource_descriptors(datapackage["resources"])
        return datapackage

    def _filter_resource_descriptors(self, descriptors):
        return [self._filter_resource_descriptor(descriptor) for descriptor in descriptors]

    def _filter_resource_descriptor(self, descriptor):
        return descriptor

    def _filter_resources(self, resources, datapackage):
        for i, resource in enumerate(resources):
            resource_descriptor = datapackage["resources"][i]
            yield self._filter_resource(resource, resource_descriptor)

    def _filter_resource(self, resource, descriptor):
        for row in resource:
            try:
                filtered_row = self._filter_row(row, descriptor)
            except Exception:
                logging.info(json.dumps(row))
                raise
            if filtered_row is not None:
                yield filtered_row

    def _filter_row(self, row, resource_descriptor):
        return row

    def _process(self, datapackage, resources):
        datapackage = self._filter_datapackage(datapackage)
        resources = self._filter_resources(resources, datapackage)
        return super(FilterResourcesProcessor, self)._process(datapackage, resources)


class BaseDownloadProcessor(AddResourcesProcessor):

    def _get_resource_descriptors(self):
        return [{"name": self._get_source_name(),
                 "path": "{}.csv".format(self._get_source_name()),
                 "schema": self._get_schema()}]

    def _get_resources_iterator(self):
        if self._parameters.get("mock"):
            return [self._mock_download()]
        else:
            return [self._download()]

    def _get_schema(self):
        raise NotImplementedError()

    def _download(self):
        raise NotImplementedError()

    def _mock_download(self):
        raise NotImplementedError()

    def _get_source_name(self):
        raise NotImplementedError()
