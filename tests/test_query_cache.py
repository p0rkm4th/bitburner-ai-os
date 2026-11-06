import unittest

from app.query_cache import cached_query_result, remember_query_result


class QueryCacheTests(unittest.TestCase):
    def test_long_queries_with_same_prefix_do_not_collide(self):
        state = {}
        prefix = "TypeError: failed while evaluating Netscript operation " + ("x" * 300)
        first = prefix + "ns.grow is not a function"
        second = prefix + "ns.weaken is not a function"

        remember_query_result(state, "game_troubleshoot", first, "Advice for grow")
        remember_query_result(state, "game_troubleshoot", second, "Advice for weaken")

        self.assertEqual(cached_query_result(state, "game_troubleshoot", first), "Advice for grow")
        self.assertEqual(cached_query_result(state, "game_troubleshoot", second), "Advice for weaken")


if __name__ == "__main__":
    unittest.main()
