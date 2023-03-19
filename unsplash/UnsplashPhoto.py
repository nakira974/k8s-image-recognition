import os
import datasets

_CITATION = """\
@InProceedings{huggingface:dataset,
title = {Unsplash Lite Dataset 1.2.0 Photos},
author={Unsplash},
year={2022}
}
"""

_DESCRIPTION = """\
This is a dataset that streams photos data from the Unsplash 25K servers.
"""
_HOMEPAGE = "https://github.com/unsplash/datasets/"

_LICENSE = ""

_URL = "https://unsplash.com/data/lite/latest"


class UnsplashPhoto(datasets.GeneratorBasedBuilder):
    """The Unsplash 25K dataset for photos"""

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    'photo_id': datasets.Value("string"),
                    'photo_url': datasets.Value("string"),
                    'photo_image_url': datasets.Value("string"),
                    'photo_submitted_at': datasets.Value("string"),
                    'photo_featured': datasets.Value("string"),
                    'photo_width': datasets.Value("int32"),
                    'photo_height': datasets.Value("int32"),
                    'photo_aspect_ratio': datasets.Value("float32"),
                    'photo_description': datasets.Value("string"),
                    'photographer_username': datasets.Value("string"),
                    'photographer_first_name': datasets.Value("string"),
                    'photographer_last_name': datasets.Value("string"),
                    'exif_camera_make': datasets.Value("string"),
                    'exif_camera_model': datasets.Value("string"),
                    'exif_iso': datasets.Value("string"),
                    'exif_aperture_value': datasets.Value("string"),
                    'exif_focal_length': datasets.Value("string"),
                    'exif_exposure_time': datasets.Value("string"),
                    'photo_location_name': datasets.Value("string"),
                    'photo_location_latitude': datasets.Value("string"),
                    'photo_location_longitude': datasets.Value("string"),
                    'photo_location_country': datasets.Value("string"),
                    'photo_location_city': datasets.Value("string"),
                    'stats_views': datasets.Value("int32"),
                    'stats_downloads': datasets.Value("int32"),
                    'ai_description': datasets.Value("string"),
                    'ai_primary_landmark_name': datasets.Value("string"),
                    'ai_primary_landmark_latitude': datasets.Value("string"),
                    'ai_primary_landmark_longitude': datasets.Value("string"),
                    'ai_primary_landmark_confidence': datasets.Value("string"),
                    'blur_hash': datasets.Value("string"),
                }
            ),
            supervised_keys=None,
            homepage="https://github.com/unsplash/datasets/",
            citation=_CITATION,
        )

    def _split_generators(self, dl_manager):
        new_url = dl_manager.download_and_extract(_URL)
        # remove extra files
        for file in os.listdir(new_url):
            if os.path.isfile(new_url + "/" + file):
                if file != 'photos.tsv000':
                    os.remove(new_url + '/' + file)
        return [
            datasets.SplitGenerator(
                name=datasets.Split.TRAIN,
                gen_kwargs={"filepath": os.path.join(new_url, "photos.tsv000")}
            ),
        ]

    def _generate_examples(self, filepath):
        """This function returns the examples in the raw (text) form."""
        with open(filepath, "r") as f:
            id_ = 0
            for line in f:
                if id_ == 0:
                    cols = line.strip().split("\t")
                    id_ += 1
                else:
                    values = line.strip().split("\t")
                    if len(values) != len(cols):
                        values.extend([''] * (len(cols) - len(values)))
                    yield id_, {cols[i]: values[i] for i in range(len(cols))}
                    id_ += 1
