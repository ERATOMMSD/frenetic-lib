from typing import List

import numpy as np
import pytest

from freneticlib.representations.abstract_representation import RoadRepresentation


class RoadRepresentation_TestImpl(RoadRepresentation):
    """Implements Abstract RoadRepresentation class, so we can test it"""

    def get_value(self, previous: List = None) -> int:
        return 0

    def to_cartesian(self, test):
        return []


class TestAbstractRoadRepresentation(object):
    @pytest.mark.parametrize("length", [1, 5, 10, 11, 50, 100])
    def test_get_length_with_no_variation(self, length):
        variation = 0
        gen = RoadRepresentation_TestImpl(length=length, variation=variation)
        assert gen.get_length() == length

    def test_zero_length_raises_exception(self):
        with pytest.raises(ValueError):
            gen = RoadRepresentation_TestImpl(length=0, variation=0)

    @pytest.mark.parametrize("length", [6, 10, 11, 50, 100])
    def test_get_length_with_variation(self, length):
        variation = 5
        gen = RoadRepresentation_TestImpl(length=length, variation=variation)
        lengths = np.array(
            [gen.get_length() for _ in range(100_000)]
        )  # get 100'000 test lengths, make sure that they're in the range
        out_of_range = lengths[(lengths < length - variation) | (length >= length + variation)]
        assert (
            sum(lengths == (length - variation)) > 0
        )  # check if some of the 100k are at the start  (might fail if we are very unlucky)
        assert (
            sum(lengths == (length + variation)) > 0
        )  # check if some of the 100k are at the end  (might fail if we are very unlucky)
        assert len(out_of_range) == 0

    @pytest.mark.parametrize("length", [1, 5, 10, 11, 50, 100])
    def test_generate_check_length_no_variation(self, length):
        variation = 0
        gen = RoadRepresentation_TestImpl(length=length, variation=variation)
        test = gen.generate()
        assert len(test) == length
