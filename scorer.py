import datetime
from dateutil.parser import parse
import re

class Scorer:
    """Calculates a 'freshness' score for a dataset."""

    def calculate_freshness_score(self, date_clues, title_clues):
        """
        Calculates a numerical freshness score from 0-100.

        Args:
            date_clues (list): A list of text snippets that might contain dates.
            title_clues (list): A list of text snippets from the title.

        Returns:
            int: A freshness score from 0-100, or None.
        """
        # Rule 3: Check for real-time keywords
        for clue in date_clues + title_clues:
            if any(keyword in clue.lower() for keyword in ['real-time', 'daily', 'live']):
                return 95

        # Rule 1: Primary Signal - Explicit "Last Modified/Updated" date
        best_date = None
        for clue in date_clues:
            try:
                # A simple regex to find dates near keywords
                match = re.search(r'(?i)(?:updated|modified|published)(?:\s*on)?\s*[:\-]?\s*(.*)', clue)
                if match:
                    date_str = match.group(1).strip()
                    parsed_date = parse(date_str, fuzzy=True)
                    if not best_date or parsed_date > best_date:
                        best_date = parsed_date
            except (ValueError, TypeError):
                continue

        if best_date:
            days_since_update = (datetime.datetime.now() - best_date).days
            if days_since_update < 0: # Date is in the future, treat as very fresh
                days_since_update = 0
            score = 100 * (0.99 ** days_since_update)
            return int(score)

        # Rule 2: Secondary Signal - Year in the title
        current_year = datetime.datetime.now().year
        best_year = 0
        for clue in title_clues:
            # Find 4-digit numbers that look like years (e.g., 1999, 2023)
            years = re.findall(r'\b(19\d{2}|20\d{2})\b', clue)
            for year_str in years:
                year = int(year_str)
                # Consider any year from the past up to one year in the future
                if year <= current_year + 1:
                    if year > best_year:
                        best_year = year

        if best_year > 0:
            year_diff = current_year - best_year
            if year_diff < 0: # Future year
                return 90
            score = 90 - (year_diff * 15) # Decrease score by 15 for each year old
            return max(0, score)

        # Rule 4: No signal found
        return 20