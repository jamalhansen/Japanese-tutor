from typing import Tuple

class SM2:
    @staticmethod
    def calculate_next_review(
        rating: int,
        repetitions: int,
        interval: int,
        easiness_factor: float
    ) -> Tuple[int, int, float]:
        """
        Calculates the next interval, repetition count, and easiness factor using the SM-2 algorithm.
        
        Args:
            rating: 0-5 (0: Again, 1: Again, 2: Again, 3: Hard, 4: Good, 5: Easy)
            repetitions: number of times the card has been reviewed
            interval: current interval in days
            easiness_factor: current easiness factor
            
        Returns:
            (new_interval, new_repetitions, new_easiness_factor)
        """
        # SM-2 treats 0, 1, 2 as "incorrect" (Again)
        if rating < 3:
            new_repetitions = 0
            new_interval = 1
        else:
            if repetitions == 0:
                new_interval = 1
            elif repetitions == 1:
                new_interval = 6
            else:
                new_interval = round(interval * easiness_factor)
            new_repetitions = repetitions + 1

        # Update easiness factor
        new_easiness_factor = easiness_factor + (0.1 - (5 - rating) * (0.08 + (5 - rating) * 0.02))
        
        # Min easiness factor is 1.3
        if new_easiness_factor < 1.3:
            new_easiness_factor = 1.3
            
        return new_interval, new_repetitions, new_easiness_factor
