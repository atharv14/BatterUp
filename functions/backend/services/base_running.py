from typing import List, Tuple, Dict
from models.schemas.game import BaseState, BaseRunner, RunnerAdvancement, PlayResult

class BaseRunningService:
    @staticmethod
    def advance_runners(
        current_bases: BaseState,
        batter_id: str,
        hit_type: str
    ) -> Tuple[BaseState, List[RunnerAdvancement], int]:
        """
        Advance runners based on hit type
        Returns: (new_base_state, advancements, runs_scored)
        """
        advancements = []
        runs_scored = 0
        new_bases = BaseState()

        # Get current runners
        runners = current_bases.get_runners()
        
        # Handle different hit types
        if hit_type == "home_run":
            # Score all runners and batter
            for base, runner in runners:
                advancements.append(
                    RunnerAdvancement(
                        runner=runner,
                        from_base=base,
                        to_base="home",
                        scored=True
                    )
                )
                runs_scored += 1
            
            # Add batter's home run
            advancements.append(
                RunnerAdvancement(
                    runner=BaseRunner(player_id=batter_id, starting_base=0),
                    from_base="home",
                    to_base="home",
                    scored=True
                )
            )
            runs_scored += 1

        elif hit_type == "triple":
            # Score all runners
            for base, runner in runners:
                advancements.append(
                    RunnerAdvancement(
                        runner=runner,
                        from_base=base,
                        to_base="home",
                        scored=True
                    )
                )
                runs_scored += 1
            
            # Place batter on third
            new_bases.third = BaseRunner(
                player_id=batter_id,
                starting_base=0
            )
            advancements.append(
                RunnerAdvancement(
                    runner=BaseRunner(player_id=batter_id, starting_base=0),
                    from_base="home",
                    to_base="third",
                    scored=False
                )
            )

        elif hit_type == "double":
            # Score runners from second and third
            for base, runner in runners:
                if base in ["second", "third"]:
                    advancements.append(
                        RunnerAdvancement(
                            runner=runner,
                            from_base=base,
                            to_base="home",
                            scored=True
                        )
                    )
                    runs_scored += 1
                elif base == "first":
                    new_bases.third = runner
                    advancements.append(
                        RunnerAdvancement(
                            runner=runner,
                            from_base="first",
                            to_base="third",
                            scored=False
                        )
                    )
            
            # Place batter on second
            new_bases.second = BaseRunner(
                player_id=batter_id,
                starting_base=0
            )
            advancements.append(
                RunnerAdvancement(
                    runner=BaseRunner(player_id=batter_id, starting_base=0),
                    from_base="home",
                    to_base="second",
                    scored=False
                )
            )

        elif hit_type == "single":
            # Score runner from third
            for base, runner in runners:
                if base == "third":
                    advancements.append(
                        RunnerAdvancement(
                            runner=runner,
                            from_base="third",
                            to_base="home",
                            scored=True
                        )
                    )
                    runs_scored += 1
                elif base == "second":
                    new_bases.third = runner
                    advancements.append(
                        RunnerAdvancement(
                            runner=runner,
                            from_base="second",
                            to_base="third",
                            scored=False
                        )
                    )
                elif base == "first":
                    new_bases.second = runner
                    advancements.append(
                        RunnerAdvancement(
                            runner=runner,
                            from_base="first",
                            to_base="second",
                            scored=False
                        )
                    )
            
            # Place batter on first
            new_bases.first = BaseRunner(
                player_id=batter_id,
                starting_base=0
            )
            advancements.append(
                RunnerAdvancement(
                    runner=BaseRunner(player_id=batter_id, starting_base=0),
                    from_base="home",
                    to_base="first",
                    scored=False
                )
            )

        return new_bases, advancements, runs_scored

    @staticmethod
    def get_rbi_count(advancements: List[RunnerAdvancement]) -> int:
        """Calculate RBIs from runner advancements"""
        return sum(1 for adv in advancements if adv.scored)