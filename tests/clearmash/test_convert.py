from datapackage_pipelines_mojp.clearmash.processors.convert import Processor
from .mock_clearmash_api import MockClearmashApi
from ..common import get_mock_settings, assert_processor, assert_dict
from .test_download import get_downloaded_docs
from datapackage_pipelines_mojp.clearmash.api import parse_clearmash_documents


class MockProcessor(Processor):

    def _get_clearmash_api(self):
        return MockClearmashApi()

    def _get_parsed_docs(self, item_ids):
        # this function gets the parsed doc for each item from DB
        # here we make an API call via the mock api to get this data
        # limit to specific ids to prevent keeping too much mock data
        allowed_item_ids = ['134330', '194827', '171827', '205406', '225613', '219323', '215277', '169923', '262509',
                            '213914', '258864', '249438', '201098', '239808', '235245', '192141', '223656', '169695']
        item_ids = [id for id in item_ids if id in allowed_item_ids]
        if len(item_ids) > 0:
            for doc in parse_clearmash_documents(self._get_clearmash_api().get_documents(item_ids)):
                yield {"item_id": doc["item_id"], "parsed_doc": doc["parsed_doc"]}

    def _get_related_doc_item_ids(self, all_document_ids):
        # this function looks up document ids in DB and matches to item id
        mock_map = {"c2e63d08be2a41b79b7b4d888de733cd": 128003,
                    "0ed7aabcfe8e4b1ca1d06e07de2e329f": 183716,
                    "74a7cbfd4a214312b0ab9bd5fc978a3c": 127841,
                    "130dee5e319946b3acc145d3626b65c2": 137736,
                    "d06a9600c15349179abe05ff2352d84e": 134330,
                    "40776e787d424a22b977e07fd64452ad": 181747,
                    "91124485965644e78197c9bc838d933d": 169695,
                    "ef803db0b02449eabf5471464e80a150": 169923,
                    "a924181cdf524e24964731d2a9e9e2a0": 192141,
                    "3fb833c8d01a45d29e190f625856cb40": 194827,
                    "00be8d5798bc4e65877f222896668b93": 201098,
                    "a0d0dd3bfa34485cb9684047ed29fcd4": 205406,
                    "c78152ce6f0849b39f550d41b0e19f13": 213914,
                    "15ff1fcb2bf34e5abc5e110976eb971a": 215277,
                    "6f21984792a344b3a7b3e32ef889abbd": 219323,
                    "797cb4eec1344ea589cd28967a48185f": 223656,
                    "b5ef0603fab44b01b76823d45164efec": 225613,
                    "983b93b7da2a4783b44b3894cfa8dfa5": 235245,
                    "d958b31a5c5542f0bf9292ed9fff5fbd": 239808,
                    "63227eab3ac342c7b13decce573a654a": 249438,
                    "0dd0a8e1a5e0407d9eda85668a79da02": 258864,
                    "3a601d9b74934cdebcf8fc2fec9e517b": 206455,
                    "e20282b830bb4c44b48ede006026009a": 124987,
                    "748a55c7b7e448dd9879af75c134f8c4": 135520,
                    "ee68252780e0480f95f35f8a9fe9a7c7": 202556,
                    "6a7b667acad1491faf4f9eeaf6d5ba3f": 229866,
                    "cd6cfd1166614c4fac7dd22bc660dd81": 251905,
                    "57397f1bd68943b0b0b10540748a6f30": 171827,
                    "7956bbfba88c4f83be11c941f99ad0cc": 233332,
                    "e4ec5b540d3349beb67cc0b1949970fb": 234428,
                    "640406bd20f8484089cca688958c1c5b": 196729,
                    "3a008872a291448fad7caf41dda33581": 244137,
                    "d9b96f8b5eb642a183bf67359e7a31bd": 262509,
                    "a7f9015605144778a95c222886f2e174": 176709,
                    "aeb9cf3f2c364f8fb07f22ad26a77895": 124268,
                    "a539f373ac124e42942982a762092e05": 248579,
                    "52ea28a500e94f639345b7486720acbf": 115364,
                    "d750f0eec2f9490eb6b73ba2d1a0fc23": 125077,
                    "d7103f57950e4068a97be01ed65b95b9": 129911,
                    "7ae510e8c4324182a776496e5590903d": 131708,
                    "a58554d922af456a87d31a351324448f": 138801,
                    "d1e730557c1b443792d8582859420721": 139545,
                    "f3eb6804f793459ebbe4e79aead2d2c9": 148156,
                    "92ce3af2188f4a2084fb21eb009fb2d6": 158067,
                    "fcd5b7acb6ef4a95b8bbddc7a613b086": 159662,
                    "a3cd24a7e9544441b8b750268e1c36e1": 186759,
                    "c92dd7eb0d6b4a1fbcbc8a81a19225f0": 187198,
                    "911292174ddf476a9b0608bc3772d81e": 189084,
                    "937945e5fdf04e85a32ff2533e2ff54c": 190715,
                    "234d0c9732524dcc90cacf1aa68d8c12": 194762,
                    "b14a3000f1cb49189a1e69f937482065": 208709,
                    "69140514767848b4a04f48e8f6600841": 217322,
                    "c596a64214954ea1ac7f03b371e0005d": 219720,
                    "e0a1500d9bf3488d8d6b0d47f8c3022c": 219762,
                    "4a46c0cc158b41c4af205718bc83c703": 222395,
                    "eaddbe65cf1e46bb80787d8ee5d9df14": 223548,
                    "59fc85fe74894f5b9a4a110b2d3732e0": 225465,
                    "d0cd975527b444e5a9e9a9e7cb132f32": 225781,
                    "6f36ba78bed74af3b0bd0dfccbec3154": 226996,
                    "b3c734a32af04a4089a58abc90bc7203": 228301,
                    "0f74b39fc8a84e46b3c17f9804fe9037": 242145,
                    "b4c02af18643427d9abb2a6a379df8fa": 259961,}
        res = {}
        for doc_id in all_document_ids:
            if doc_id in mock_map:
                res[doc_id] = mock_map[doc_id]
        return res

def get_clearmash_convert_resource_data(downloaded_docs=None):
    if not downloaded_docs:
        downloaded_docs = get_downloaded_docs()
        expected_len = 5
    else:
        expected_len = None
    processor = MockProcessor(parameters={"input-resource": "entities", "output-resource": "dbs-docs"},
                              datapackage={"resources": [{"name": "entities"}]},
                              resources=[downloaded_docs],
                              settings=get_mock_settings())
    docs = assert_processor(processor)
    if expected_len:
        assert len(docs) == expected_len
    return docs


def test_clearmash_convert():
    resource = get_clearmash_convert_resource_data()
    assert len(resource) == 5
    assert len(resource[0].pop("content_html_he")) == 1060
    assert len(resource[0].pop("content_html_en")) == 1399
    assert_dict(resource[0], {"collection": "familyNames",
                              "content_html": {},
                              "title_en": "BEN AMARA",
                              "title_he": "בן עמרה",
                              "title": {},
                              "id": "115306",
                              "source": "clearmash",
                              "version": "6468918-f91ea044052746a2903d6ee60d9b374b",
                              "related_documents": {},
                              "main_image_url": "",
                              "main_thumbnail_image_url": "",
                              "keys": ['source_doc'],
                              "images": [],
                              "geo_location": ""})
    assert_dict(resource[1], {"collection": "places"})
    assert_dict(resource[2], {"collection": "movies"})
    assert_dict(resource[3], {"collection": "personalities"})
    assert_dict(resource[4],
                {"collection": "photoUnits", "id": "115301",
                 "main_image_url": "https://bhfiles.clearmash.com/MediaServer/Images/5ff94861dad3480c9e59f1904a825caf_1024x1024.JPG",
                 "main_thumbnail_image_url": "https://bhfiles.clearmash.com/MediaServer/Images/5ff94861dad3480c9e59f1904a825caf_260x260.JPG"})

def test_clearmash_convert_photoUnits():
    entity_ids = [{"item_id": 203884, "collection": "photoUnits"},]
    resource = get_clearmash_convert_resource_data(get_downloaded_docs(entity_ids))
    assert len(resource) == 1
    image_url = lambda str: 'https://bhfiles.clearmash.com/MediaServer/Images/{}'.format(str)
    assert_dict(resource[0], {'main_image_url': image_url("fff406c76ce942f9a37a19dcc061a36b_1024x1024.JPG"),
                              'main_thumbnail_image_url': image_url("fff406c76ce942f9a37a19dcc061a36b_260x260.JPG")})
    assert resource[0]["images"] == [image("fff406c76ce942f9a37a19dcc061a36b"),
                                     image("a47cdc2e717045c5b3afadbcdf3d8a1d"),
                                     image("3dd9530eb0554cc59345da164522b51d"),
                                     image("c6d0e13b4c81460cb6d7405808ad138c"),]

def image(id):
    return {'url': 'https://bhfiles.clearmash.com/MediaServer/Images/{}_1024x1024.JPG'.format(id),
            'thumbnail_url': 'https://bhfiles.clearmash.com/MediaServer/Images/{}_260x260.JPG'.format(id)}

def test_clearmash_convert_place_with_related_photoUnits():
    entity_ids = [{"item_id": 233953, "collection": "places"},]
    resource = get_clearmash_convert_resource_data(get_downloaded_docs(entity_ids))
    assert len(resource) == 1
    assert_dict(resource[0], {'main_image_url': image("031017ece2cc49d2ba73311e336408a2")["url"],
                              'main_thumbnail_image_url': image("031017ece2cc49d2ba73311e336408a2")["thumbnail_url"],})
    assert resource[0]["images"][:3] == [image("031017ece2cc49d2ba73311e336408a2"),
                                          image("1245931e49264167a801a8f31a24eaed"),
                                          image("49efc3eb16e44689b5dd9b4b078201ec"),]

def test_geocode_location():
    # places sude have location
    entity_ids = [{"item_id": 233953, "collection": "places"},]
    resource = get_clearmash_convert_resource_data(get_downloaded_docs(entity_ids))
    assert_dict(resource[0], {'title_en': 'Moscow'})
    assert_dict(resource[0], {'geo_location': 'Moscow'})
    # other collections should have an empty string
    entity_ids = [{"item_id": 203884, "collection": "photoUnits"},]
    resource = get_clearmash_convert_resource_data(get_downloaded_docs(entity_ids))
    assert_dict(resource[0], {'title_en': 'The Rema Synagogue, Cracow, Poland. Model. Permanent Exhibitio'})
    assert_dict(resource[0], {'geo_location': ''})



