"""
Treasury Agent — orchestration entry point for DAO treasury recommendations.
Runs: mandate → discovery → risk → decision → explanation → proposal → audit.
No autonomous execution in MVP.
"""

from .run import run_treasury_recommendation

__all__ = ["run_treasury_recommendation"]
