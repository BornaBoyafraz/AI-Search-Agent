import unittest
from unittest.mock import patch

from agent.search import search_web


class SearchWebTests(unittest.TestCase):
    @patch("agent.search._ddg_lite_search", return_value=[])
    @patch("agent.search._ddg_html_search", return_value=[])
    @patch("agent.search._collect_results")
    def test_duckduckgo_provider_sorts_by_score(self, mock_collect, _mock_html, _mock_lite):
        mock_collect.return_value = [
            {
                "url": "https://example.com/b",
                "title": "B",
                "snippet": "",
                "domain": "example.com",
                "score": 1,
            },
            {
                "url": "https://agency.gov/a",
                "title": "A",
                "snippet": "",
                "domain": "agency.gov",
                "score": 8,
            },
        ]

        results = search_web("policy", max_results=5, provider="duckduckgo", safe_search=True)

        self.assertEqual(results[0]["url"], "https://agency.gov/a")
        self.assertEqual(results[1]["url"], "https://example.com/b")
        mock_collect.assert_called()

    @patch("agent.search._wiki_search")
    @patch("agent.search._google_cse_search")
    @patch("agent.search._collect_results")
    def test_wikipedia_provider_only_calls_wikipedia(self, mock_collect, mock_google, mock_wiki):
        mock_wiki.return_value = [
            {
                "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                "title": "Python",
                "snippet": "A programming language",
                "domain": "en.wikipedia.org",
                "score": 4,
            }
        ]

        results = search_web("python", max_results=3, provider="wikipedia", safe_search=False)

        self.assertEqual(len(results), 1)
        mock_wiki.assert_called_once()
        mock_collect.assert_not_called()
        mock_google.assert_not_called()

    @patch("agent.search._wiki_search")
    @patch("agent.search._ddg_lite_search")
    @patch("agent.search._ddg_html_search")
    @patch("agent.search._google_cse_search")
    @patch("agent.search._collect_results")
    def test_auto_provider_falls_back_to_wikipedia(
        self,
        mock_collect,
        mock_google,
        mock_html,
        mock_lite,
        mock_wiki,
    ):
        mock_collect.side_effect = RuntimeError("ddg unavailable")
        mock_google.return_value = []
        mock_html.return_value = []
        mock_lite.return_value = []
        mock_wiki.return_value = [
            {
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                "title": "Artificial intelligence",
                "snippet": "",
                "domain": "en.wikipedia.org",
                "score": 4,
            }
        ]

        results = search_web("ai", provider="auto")

        self.assertEqual(results[0]["domain"], "en.wikipedia.org")
        self.assertTrue(mock_collect.called)
        mock_wiki.assert_called_once()


if __name__ == "__main__":
    unittest.main()
