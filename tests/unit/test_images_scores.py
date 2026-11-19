from unittest.mock import patch

from clutch import images


class Picture:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def convert(self, mode):
        return self


def test_scores_uses_shared_helpers_and_absent_kinds():
    image = type("Image", (), {"open": staticmethod(lambda path: Picture())})
    with (
        patch.object(images, "_load", return_value=(image, None, None, None, None)),
        patch.object(images, "_preservation", return_value=0.71) as ssim,
        patch.object(images, "_presence", side_effect=[6, 8]) as orb,
    ):
        assert images.scores("candidate", ["base", "one", "two"]) == (0.71, 14)
        assert ssim.call_count == 1 and orb.call_count == 2
        assert images.scores("candidate", []) == (None, None)
