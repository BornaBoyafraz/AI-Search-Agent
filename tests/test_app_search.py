import unittest
from unittest.mock import patch

from agent.models import SearchResponse, SearchResult
from ui_agent import run_agent, run_agent_response


class RunAgentTests(unittest.TestCase):
    @patch("ui_agent.SearchEngine.run")
    def test_returns_answer_for_single_result(self, mock_run):
        mock_run.return_value = SearchResponse(
            query="python",
            results=[SearchResult(title="Python", snippet="", url="https://python.org")],
            summary="Python is a programming language.",
            sources=["https://python.org"],
            error=None,
        )

        output = run_agent("python")

        self.assertIsInstance(output, str)
        self.assertIn("programming language", output)

    @patch("ui_agent.SearchEngine.run")
    def test_returns_structured_results_for_multiple_results(self, mock_run):
        mock_run.return_value = SearchResponse(
            query="ai",
            results=[
                SearchResult(title="A", snippet="", url="https://a.example"),
                SearchResult(title="B", snippet="", url="https://b.example"),
            ],
            summary="summary",
            sources=[],
            error=None,
        )

        output = run_agent_response("ai")

        self.assertTrue(output.is_list)
        self.assertEqual(len(output.results), 2)

    @patch("ui_agent.SearchEngine.run")
    def test_raises_runtime_error_when_no_results(self, mock_run):
        mock_run.return_value = SearchResponse(
            query="none",
            results=[],
            summary="fallback",
            sources=[],
            error="No results were returned.",
        )

        with self.assertRaises(RuntimeError):
            run_agent("none")


if __name__ == "__main__":
    unittest.main()
