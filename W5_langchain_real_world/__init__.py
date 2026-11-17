"""
W5_langchain_real_world Package
Real-world cross-domain agent workload integrating SQLite and long document reasoning via LangChain.
"""

from W5_langchain_real_world.agent import run_w5_trial
from W5_langchain_real_world.evaluator import evaluate_quality

__all__ = ["run_w5_trial", "evaluate_quality"]
