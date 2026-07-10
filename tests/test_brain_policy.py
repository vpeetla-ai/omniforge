
from omniforge.brain.policy import bucket_for_agent
from omniforge.models import RouteBucket


def test_buckets():
    assert bucket_for_agent("web") == RouteBucket.FAST
    assert bucket_for_agent("api") == RouteBucket.STRUCTURED
    assert bucket_for_agent("analysis") == RouteBucket.REASONING
    assert bucket_for_agent("vision") == RouteBucket.VISION
