import unittest
from unittest.mock import patch
import datetime
from scorer import Scorer

class TestScorer(unittest.TestCase):

    def setUp(self):
        """Set up the Scorer instance."""
        self.scorer = Scorer()

    def test_real_time_keywords(self):
        """Test that 'real-time', 'daily', 'live' keywords give a high score."""
        self.assertEqual(self.scorer.calculate_freshness_score(['live data feed'], []), 95)
        self.assertEqual(self.scorer.calculate_freshness_score([], ['daily updates']), 95)
        self.assertEqual(self.scorer.calculate_freshness_score(['real-time metrics'], ['some title']), 95)

    @patch('scorer.datetime')
    def test_explicit_date(self, mock_dt):
        """Test score calculation based on explicit 'last updated' dates."""
        mock_now = datetime.datetime(2025, 9, 27)
        mock_dt.datetime.now.return_value = mock_now

        # A date from 2 days ago should be high.
        score_recent = self.scorer.calculate_freshness_score(['Last Updated: 2025-09-25'], [])
        expected_recent_score = int(100 * (0.99 ** 2)) # 98
        self.assertEqual(score_recent, expected_recent_score)

        # A date from exactly one year ago.
        score_old = self.scorer.calculate_freshness_score(['Modified on: 2024-09-27'], [])
        expected_old_score = int(100 * (0.99 ** 365)) # 2
        self.assertEqual(score_old, expected_old_score)

    @patch('scorer.datetime')
    def test_year_in_title(self, mock_dt):
        """Test score calculation based on a year in the title."""
        mock_now = datetime.datetime(2025, 9, 27)
        mock_dt.datetime.now.return_value = mock_now

        self.assertEqual(self.scorer.calculate_freshness_score([], ['2025 Annual Crime Report']), 90)
        self.assertEqual(self.scorer.calculate_freshness_score([], ['City Budget 2024 Data']), 75)
        self.assertEqual(self.scorer.calculate_freshness_score([], ['Historical Data (2019)']), 0)

    def test_no_signal(self):
        """Test the default score when no clues are found."""
        self.assertEqual(self.scorer.calculate_freshness_score([], []), 20)
        self.assertEqual(self.scorer.calculate_freshness_score(['some random text'], ['a plain title']), 20)

    @patch('scorer.datetime')
    def test_prioritization(self, mock_dt):
        """Test that explicit dates are prioritized over years in title."""
        mock_now = datetime.datetime(2025, 9, 27)
        mock_dt.datetime.now.return_value = mock_now

        score = self.scorer.calculate_freshness_score(
            ['Updated: 2024-12-25'],
            ['2025 Annual Report']
        )
        # The score should be based on the 2024 date, not the 2025 title.
        days_diff = (mock_now - datetime.datetime(2024, 12, 25)).days
        expected_score = int(100 * (0.99 ** days_diff))
        self.assertEqual(score, expected_score)


if __name__ == '__main__':
    unittest.main()